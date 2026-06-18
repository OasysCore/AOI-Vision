#!/usr/bin/env bash
# AOI-Vision E01 即梦全场景自动生成脚本
# 用法: bash dreamina_gen_e01.sh

set -e
CLI="$HOME/.dreamina_cli/dreamina_cli"
OUT="$HOME/Desktop/AOI-E01-素材"
mkdir -p "$OUT"

# ========== B1: 工厂产线 ==========
echo ">>> B1 工厂产线..."
B1=$($CLI text2video \
  --prompt="A tired factory quality inspector under warm yellow lights, examining electronic parts through magnifying glass. Shot from side. Fatigue visible. Documentary style." \
  --ratio=9:16 --duration=4 --poll=60 2>&1)
echo "$B1" | grep submit_id && echo "✅ B1 submitted"

# ========== B2: 检测系统 ==========
echo ">>> B2 检测系统..."
B2=$($CLI text2video \
  --prompt="Futuristic automated inspection machine scanning green PCB. Blue laser scanning line. Digital HUD green PASS. Dark high-tech environment dramatic blue lighting." \
  --ratio=9:16 --duration=4 --poll=60 2>&1)
echo "$B2" | grep submit_id && echo "✅ B2 submitted"

# ========== B3: 缺陷检出 ==========
echo ">>> B3 缺陷检出..."
B3=$($CLI text2video \
  --prompt="Macro close-up of PCB defect. Three red circles appear: cracked solder joint, scratched trace, oxidized pad. Status changes to red FAIL. Dark background high contrast." \
  --ratio=9:16 --duration=4 --poll=60 2>&1)
echo "$B3" | grep submit_id && echo "✅ B3 submitted"

# ========== B4: 效率对比 ==========
echo ">>> B4 效率对比..."
B4=$($CLI text2video \
  --prompt="Split screen. Left slow manual inspection with magnifier. Right automated system rapidly processing green PASS flashing. Timer overlay 3 min vs 2.8 sec. Professional style." \
  --ratio=9:16 --duration=4 --poll=60 2>&1)
echo "$B4" | grep submit_id && echo "✅ B4 submitted"

# ========== F1: 结尾封面图 ==========
echo ">>> F1 结尾封面..."
F1=$($CLI text2image \
  --prompt="Dark background subtle technology grid. Blue cyan accent lights. Clean minimalist. Ample negative space for text overlay. Industrial aesthetic." \
  --ratio=9:16 --poll=60 2>&1)
echo "$F1" | grep submit_id && echo "✅ F1 submitted"

echo ""
echo "======== 全部提交完成 ========"
echo "输出目录: $OUT"
echo ""
echo "下一步: 在即梦App录制数字人 D1/D2/D3 → 导入剪映合成"
