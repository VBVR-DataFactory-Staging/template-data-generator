#!/bin/bash

echo "📦 准备推送 O-4_shape_matching_data-generator 到 GitHub"
echo ""
echo "请选择推送目标："
echo "1) vm-dataset/O-4_shape_matching_data-generator (推荐)"
echo "2) jyizheng/O-4_shape_matching_data-generator (个人账户)"
echo ""
read -p "请输入选项 (1 或 2): " choice

case $choice in
  1)
    REPO_URL="https://github.com/vm-dataset/O-4_shape_matching_data-generator.git"
    echo ""
    echo "⚠️  请先在浏览器中创建仓库："
    echo "   https://github.com/organizations/vm-dataset/repositories/new"
    echo ""
    echo "仓库设置："
    echo "  - Name: O-4_shape_matching_data-generator"
    echo "  - Description: Shape matching task data generator for visual reasoning dataset"
    echo "  - Public"
    echo "  - 不要初始化任何文件"
    echo ""
    read -p "已创建？按Enter继续... "
    ;;
  2)
    REPO_URL="https://github.com/jyizheng/O-4_shape_matching_data-generator.git"
    echo ""
    echo "⚠️  请先在浏览器中创建仓库："
    echo "   https://github.com/new"
    echo ""
    echo "仓库设置："
    echo "  - Name: O-4_shape_matching_data-generator"
    echo "  - Description: Shape matching task data generator for visual reasoning dataset"
    echo "  - Public"
    echo "  - 不要初始化任何文件"
    echo ""
    read -p "已创建？按Enter继续... "
    ;;
  *)
    echo "无效选项"
    exit 1
    ;;
esac

echo ""
echo "🔗 配置远程仓库..."
git remote add origin $REPO_URL 2>/dev/null || git remote set-url origin $REPO_URL

echo "🌿 确保在main分支..."
git branch -M main

echo "🚀 推送到GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功推送到 $REPO_URL"
    echo ""
    echo "访问仓库: ${REPO_URL%.git}"
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "   1. 是否已在GitHub上创建仓库"
    echo "   2. 是否有推送权限"
    echo "   3. 网络连接是否正常"
fi
