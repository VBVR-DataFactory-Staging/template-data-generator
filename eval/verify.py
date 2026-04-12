#!/usr/bin/env python3
"""Standalone evaluator for the default G-29 chart-extreme task."""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


STANDARD_WEIGHTS = {
    "first_frame_consistency": 0.15,
    "final_frame_accuracy": 0.35,
    "temporal_smoothness": 0.15,
    "visual_quality": 0.10,
    "task_specific": 0.25,
}


def load_video_frames(video_path: str, max_frames: int = 100) -> List[np.ndarray]:
    """Extract frames from a video file."""

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Cannot open video: %s" % video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if max_frames and max_frames < total_frames:
        indices = np.linspace(0, total_frames - 1, max_frames, dtype=int).tolist()
    else:
        indices = list(range(total_frames))

    frames = []
    for index in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        success, frame = cap.read()
        if success:
            frames.append(frame)

    cap.release()
    return frames


def load_image(path: str) -> Optional[np.ndarray]:
    if not os.path.exists(path):
        return None
    return cv2.imread(path)


def load_metadata(gt_dir: str) -> Dict[str, Any]:
    for candidate in ("metadata.json", "question_metadata.json"):
        path = os.path.join(gt_dir, candidate)
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return {}


def normalize_frame_size(frame: np.ndarray, target: np.ndarray) -> np.ndarray:
    if frame.shape == target.shape:
        return frame
    return cv2.resize(frame, (target.shape[1], target.shape[0]))


def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
    sigma1_sq = cv2.GaussianBlur(img1 ** 2, (11, 11), 1.5) - mu1 ** 2
    sigma2_sq = cv2.GaussianBlur(img2 ** 2, (11, 11), 1.5) - mu2 ** 2
    sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1 * mu2
    ssim_map = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1 ** 2 + mu2 ** 2 + c1) * (sigma1_sq + sigma2_sq + c2)
    )
    return float(ssim_map.mean())


def compute_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    mse = float(np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2))
    if mse == 0:
        return float("inf")
    return float(10 * np.log10(255 ** 2 / mse))


def compute_frame_difference(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    if frame_a.shape != frame_b.shape:
        frame_b = cv2.resize(frame_b, (frame_a.shape[1], frame_a.shape[0]))
    return float(np.mean(np.abs(frame_a.astype(np.float64) - frame_b.astype(np.float64))) / 255.0)


def evaluate_first_frame(first_frame: np.ndarray, gt_first: np.ndarray) -> float:
    ssim = compute_ssim(first_frame, gt_first)
    if ssim >= 0.95:
        return 1.0
    if ssim >= 0.85:
        return 0.8 + (ssim - 0.85) / 0.10 * 0.2
    if ssim >= 0.70:
        return 0.5 + (ssim - 0.70) / 0.15 * 0.3
    return ssim / 0.70 * 0.5


def evaluate_final_frame(final_frame: np.ndarray, gt_final: np.ndarray) -> float:
    ssim = compute_ssim(final_frame, gt_final)
    psnr = compute_psnr(final_frame, gt_final)
    psnr_score = 1.0 if psnr == float("inf") else max(0.0, min(1.0, (psnr - 20) / 20))
    return 0.7 * ssim + 0.3 * psnr_score


def evaluate_temporal_smoothness(frames: List[np.ndarray]) -> float:
    if len(frames) < 2:
        return 1.0
    diffs = [compute_frame_difference(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    std_diff = float(np.std(diffs))
    max_diff = float(np.max(diffs))
    variance_score = 1.0 - min(1.0, std_diff / 0.1)
    jump_score = 1.0 - min(1.0, max_diff / 0.3)
    return 0.6 * variance_score + 0.4 * jump_score


def evaluate_visual_quality(frames: List[np.ndarray]) -> float:
    if not frames:
        return 0.0
    scores = []
    for frame in frames[:: max(1, len(frames) // 10)]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(1.0, laplacian_var / 1000)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise_est = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))
        noise_score = 1.0 - min(1.0, noise_est / 30)
        scores.append(0.6 * sharpness + 0.4 * noise_score)
    return float(np.mean(scores))


class TaskEvaluator:
    """Rule-based evaluator for the default chart-extreme task."""

    def _red_mask(self, frame: np.ndarray) -> np.ndarray:
        bgr = frame
        return (
            (bgr[:, :, 2] >= 180)
            & (bgr[:, :, 1] <= 90)
            & (bgr[:, :, 0] <= 90)
        ).astype(np.uint8)

    def _bbox_from_mask(self, mask: np.ndarray) -> Optional[List[int]]:
        ys, xs = np.where(mask > 0)
        if len(xs) == 0 or len(ys) == 0:
            return None
        return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]

    def _box_iou(self, box_a: List[int], box_b: List[int]) -> float:
        left = max(box_a[0], box_b[0])
        top = max(box_a[1], box_b[1])
        right = min(box_a[2], box_b[2])
        bottom = min(box_a[3], box_b[3])
        intersection = max(0, right - left) * max(0, bottom - top)
        area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
        area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
        union = area_a + area_b - intersection
        if union <= 0:
            return 0.0
        return float(intersection / union)

    def _border_mask(self, shape: Tuple[int, int], box: List[int], thickness: int = 18) -> np.ndarray:
        mask = np.zeros(shape, dtype=np.uint8)
        x1, y1, x2, y2 = [int(value) for value in box]
        cv2.rectangle(mask, (x1, y1), (x2, y2), color=1, thickness=thickness)
        return mask

    def evaluate_task_specific(
        self,
        video_frames: List[np.ndarray],
        gt_first_frame: Optional[np.ndarray],
        parameters: Dict[str, Any],
    ) -> float:
        if len(video_frames) < 2 or not parameters:
            return 0.0

        expected_box = parameters.get("highlight_box")
        if not expected_box or len(expected_box) != 4:
            return 0.0

        first_mask = self._red_mask(video_frames[0])
        last_mask = self._red_mask(video_frames[-1])
        detected_box = self._bbox_from_mask(last_mask)
        if detected_box is None:
            return 0.0

        expected_box = [int(value) for value in expected_box]
        iou_score = self._box_iou(detected_box, expected_box)

        border_mask = self._border_mask(last_mask.shape[:2], expected_box)
        border_pixels = border_mask > 0
        border_recall = float(last_mask[border_pixels].mean()) if np.any(border_pixels) else 0.0

        red_outside = last_mask[border_mask == 0]
        outside_penalty = 1.0 - min(1.0, float(red_outside.mean()) * 3.0)

        first_frame_penalty = 1.0 - min(1.0, float(first_mask.mean()) * 10.0)

        has_correct_extreme = 0.0
        values = parameters.get("values") or []
        target_index = parameters.get("target_index")
        extreme_type = parameters.get("extreme_type")
        if values and target_index is not None and extreme_type in ("max", "min"):
            expected_index = values.index(max(values) if extreme_type == "max" else min(values))
            has_correct_extreme = 1.0 if int(target_index) == int(expected_index) else 0.0

        return max(
            0.0,
            min(
                1.0,
                0.45 * iou_score
                + 0.25 * border_recall
                + 0.15 * outside_penalty
                + 0.10 * first_frame_penalty
                + 0.05 * has_correct_extreme,
            ),
        )


def evaluate_single(
    video_path: str,
    gt_dir: str,
    task_evaluator: Optional[TaskEvaluator] = None,
) -> Dict[str, Any]:
    if task_evaluator is None:
        task_evaluator = TaskEvaluator()

    video_frames = load_video_frames(video_path)
    if not video_frames:
        return {"score": 0.0, "error": "Could not load video frames", "dimensions": {}}

    gt_first = load_image(os.path.join(gt_dir, "first_frame.png"))
    gt_final = load_image(os.path.join(gt_dir, "final_frame.png"))
    metadata = load_metadata(gt_dir)
    parameters = metadata.get("parameters", {})

    target = gt_first if gt_first is not None else gt_final
    if target is not None and video_frames[0].shape != target.shape:
        video_frames = [normalize_frame_size(frame, target) for frame in video_frames]

    dimensions = {}
    dimensions["first_frame_consistency"] = (
        evaluate_first_frame(video_frames[0], gt_first) if gt_first is not None else 0.5
    )
    dimensions["final_frame_accuracy"] = (
        evaluate_final_frame(video_frames[-1], gt_final) if gt_final is not None else 0.0
    )
    dimensions["temporal_smoothness"] = evaluate_temporal_smoothness(video_frames)
    dimensions["visual_quality"] = evaluate_visual_quality(video_frames)
    dimensions["task_specific"] = task_evaluator.evaluate_task_specific(
        video_frames,
        gt_first,
        parameters,
    )

    overall = sum(dimensions[key] * STANDARD_WEIGHTS[key] for key in STANDARD_WEIGHTS)
    overall = max(0.0, min(1.0, overall))
    return {
        "video_path": video_path,
        "gt_dir": gt_dir,
        "score": overall,
        "dimensions": dimensions,
    }


def find_video_gt_pairs(videos_dir: str, gt_dir: str) -> List[Tuple[str, str]]:
    pairs = []
    gt_samples = {}

    for root, _dirs, files in os.walk(gt_dir):
        if "first_frame.png" in files:
            gt_samples[os.path.basename(root)] = root

    for filename in sorted(os.listdir(videos_dir)):
        if filename.endswith(".mp4"):
            task_id = filename[:-4]
            if task_id in gt_samples:
                pairs.append((os.path.join(videos_dir, filename), gt_samples[task_id]))

    if pairs:
        return pairs

    for root, _dirs, files in os.walk(videos_dir):
        for filename in files:
            if filename.endswith(".mp4"):
                parent = os.path.basename(root)
                if parent in gt_samples:
                    pairs.append((os.path.join(root, filename), gt_samples[parent]))

    return pairs


def print_result(result: Dict[str, Any]) -> None:
    gt_name = os.path.basename(result.get("gt_dir", ""))
    print("\nTask: %s" % gt_name)

    if "error" in result:
        print("  ERROR: %s" % result["error"])
        return

    for dim, weight in STANDARD_WEIGHTS.items():
        score = result["dimensions"].get(dim, 0.0)
        print("  %-30s  %.4f  (weight: %.2f)" % (dim, score, weight))

    print("  %s" % ("-" * 50))
    print("  %-30s  %.4f" % ("Overall", result["score"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate chart-extreme videos against ground truth.")
    parser.add_argument("--video", type=str, help="Path to a single generated video")
    parser.add_argument("--gt-dir", type=str, help="Path to the GT sample folder")
    parser.add_argument("--videos-dir", type=str, help="Directory of generated videos")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON file")
    args = parser.parse_args()

    evaluator = TaskEvaluator()
    results = []

    if args.video and args.gt_dir:
        result = evaluate_single(args.video, args.gt_dir, evaluator)
        results.append(result)
        print_result(result)
    elif args.videos_dir and args.gt_dir:
        pairs = find_video_gt_pairs(args.videos_dir, args.gt_dir)
        if not pairs:
            print("No video-GT pairs found.")
            sys.exit(1)

        print("Found %d video(s) to evaluate.\n" % len(pairs))
        scores = []
        for video_path, gt_sample_dir in pairs:
            result = evaluate_single(video_path, gt_sample_dir, evaluator)
            results.append(result)
            print_result(result)
            scores.append(result["score"])

        print("\n%s" % ("=" * 55))
        print("  Mean score: %.4f  (%d videos)" % (np.mean(scores), len(scores)))
        print("%s" % ("=" * 55))
    else:
        parser.print_help()
        sys.exit(1)

    if args.output and results:
        with open(args.output, "w") as handle:
            json.dump(results, handle, indent=2, default=str)
        print("\nResults saved to %s" % args.output)


if __name__ == "__main__":
    main()
