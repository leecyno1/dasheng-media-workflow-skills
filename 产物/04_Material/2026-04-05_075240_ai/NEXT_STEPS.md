# Next Steps - Material Stage Complete

**Run ID**: 2026-04-05_075240_ai  
**Current Stage**: Material (Stage 4)  
**Status**: Planning complete, ready for execution or Rewrite

---

## Decision Point

You have completed the Material Planning phase. Choose your path forward:

### Path A: Complete P0 Materials First (Recommended)
**Time**: 1.5-2 hours  
**Benefit**: Full visual support for publication  
**Action**: Execute manual material collection

### Path B: Proceed to Rewrite Now
**Time**: Immediate  
**Benefit**: Maintain workflow momentum  
**Limitation**: Only 4 charts available (no screenshots/images)

---

## Path A: Complete P0 Materials

### What You'll Do
1. Take 9 data source screenshots (30-45 min)
2. Download 6 high-priority images (45-60 min)
3. Create 15 quality reports
4. Verify quality standards

### How to Start
```bash
# Open the quick start guide
open "/Volumes/PSSD/Projects/公众号文章/产物/04_Material/2026-04-05_075240_ai/QUICK_START.md"

# Or follow the comprehensive guide
open "/Volumes/PSSD/Projects/公众号文章/产物/04_Material/2026-04-05_075240_ai/MANUAL_EXECUTION_GUIDE.md"
```

### After Completion
1. Update MATERIAL_EXECUTION_STATUS.md with completion timestamp
2. Proceed to Path B (Rewrite stage)

---

## Path B: Proceed to Rewrite

### What You'll Do
Generate 4 platform-specific variants per topic (8 total rewrites):

**Per Topic**:
1. WeChat + luxun + hot (≥4000 words)
2. WeChat + lemon + normal (≥4000 words)
3. XHS video + luxun + hot (≥1800 words)
4. XHS video + lemon + normal (≥1800 words)

### Prerequisites
- ✅ Draft files exist for both topics
- ✅ 4 charts available for visual support
- ✅ Framework and strategy recommendations from Brief stage
- ⏳ Screenshots and images (optional, can add later)

### How to Start

**Option 1: Using Preset DNA (luxun/lemon)**
```bash
cd "${DASHENG_WORKSPACE}"

# Run rewrite with final structure inheritance
python3 scripts/rewrite_rerun_with_final_structure.py
```

**Option 2: Using Personal Style DNA (if extracted)**
```bash
cd "${DASHENG_WORKSPACE}"

# Run rewrite with personal style profile
python3 scripts/rewrite_with_personal_dna.py \
  --dna-path "${DASHENG_WORKSPACE}/风格库/{作者}/风格画像.md"
```

### Rewrite Stage Features
- ✅ Framework-driven structure (7 writing frameworks)
- ✅ Content enhancement strategies (4 strategies)
- ✅ Intelligent content expansion
- ✅ Strict word count validation
- ✅ Style DNA injection (luxun/lemon or personal)

### Expected Output
```
产物/06_Rewrite/{run_id}/
├── rewrite_manifest.json
├── topic-ai-ma-boom-q1-2026/
│   ├── meta.json
│   ├── topic-ai-ma-boom-q1-2026__rewrite_bundle.md
│   ├── wechat_luxun_hot.md (≥4000 words)
│   ├── wechat_lemon_normal.md (≥4000 words)
│   ├── xhs_video_luxun_hot.md (≥1800 words)
│   └── xhs_video_lemon_normal.md (≥1800 words)
└── topic-china-15th-five-year-plan-2026/
    ├── meta.json
    ├── topic-china-15th-five-year-plan-2026__rewrite_bundle.md
    ├── wechat_luxun_hot.md (≥4000 words)
    ├── wechat_lemon_normal.md (≥4000 words)
    ├── xhs_video_luxun_hot.md (≥1800 words)
    └── xhs_video_lemon_normal.md (≥1800 words)
```

### After Rewrite
1. Push to Feishu for editor review:
```bash
node scripts/feishu_rewrite_push.js "$(date +%F)"
```

2. Optionally return to complete remaining materials

---

## Workflow Context

### Completed Stages
1. ✅ **Intake** - Content aggregation from multiple sources
2. ✅ **Brief** - AI-generated topics with natural language titles
3. ✅ **Draft** - Framework-driven draft generation
4. ✅ **Material** - Planning complete, 4 charts generated

### Current Stage
4. **Material** - Execution ready (15 P0 items pending manual collection)

### Upcoming Stages
5. **Rewrite** - Generate 4 platform variants per topic
6. **Publish** - Video enhancement (interactive charts + motion narrative)
7. **Postmortem** - Performance analysis and lessons learned

---

## Material Status Summary

### Completed (4 items)
- ✅ chart_02_ai_funding_distribution.png (Topic 1)
- ✅ chart_03_tech_giants_spending.png (Topic 1)
- ✅ chart_01_gdp_growth_history.png (Topic 2)
- ✅ chart_03_three_pillars_investment.png (Topic 2)

### Ready for Execution (15 P0 items)
- ⏳ 9 data source screenshots (URLs prepared)
- ⏳ 6 high-priority images (sources identified)

### Planned for Later (34 items)
- 7 additional charts (P1/P2)
- 8 supplementary images (P1)
- 18 videos (P0/P1)

---

## Key Documents Reference

### For Material Execution (Path A)
- **QUICK_START.md** - Fast-track instructions
- **MANUAL_EXECUTION_GUIDE.md** - Comprehensive step-by-step
- **MATERIAL_DOWNLOAD_INSTRUCTIONS.md** - Detailed source URLs
- **SCREENSHOT_EXECUTION_PLAN.md** - Technical specifications
- **COMPLETION_CHECKLIST.md** - Progress tracking

### For Rewrite Stage (Path B)
- **CLAUDE.md** - Project overview and workflow
- **skills/dasheng-stage-rewrite/SKILL.md** - Rewrite stage specification
- **skills/dasheng-stage-rewrite/references/frameworks.md** - 7 writing frameworks
- **skills/dasheng-stage-rewrite/references/content-enhance.md** - 4 enhancement strategies

### For Status Tracking
- **MATERIAL_EXECUTION_STATUS.md** - Current state
- **STAGE_SUMMARY.md** - Complete overview
- **README.md** - Package navigation

---

## Recommendations

### If Time Permits (1.5-2 hours available)
→ **Choose Path A**: Complete P0 materials for maximum visual impact

### If Maintaining Momentum
→ **Choose Path B**: Proceed to Rewrite, return to materials later

### If Uncertain
→ **Review**: Open QUICK_START.md to see what material execution involves

---

## Support

**Questions about material execution?**  
→ See MANUAL_EXECUTION_GUIDE.md troubleshooting section

**Questions about rewrite stage?**  
→ See skills/dasheng-stage-rewrite/SKILL.md

**Need to understand workflow?**  
→ See CLAUDE.md project overview

**Want to see what's been done?**  
→ See STAGE_SUMMARY.md

---

## Quick Commands

### Check Current Materials
```bash
# List completed charts
ls -lh topic-*/charts/*.png

# Check documentation
ls -lh *.md

# Verify directory structure
tree -L 2
```

### Start Material Execution (Path A)
```bash
# Open quick start guide
open QUICK_START.md

# Or open comprehensive guide
open MANUAL_EXECUTION_GUIDE.md
```

### Start Rewrite Stage (Path B)
```bash
cd "${DASHENG_WORKSPACE}"

# Load environment
set -a; source ~/.openclaw/dasheng.env; set +a

# Run rewrite
python3 scripts/rewrite_rerun_with_final_structure.py
```

---

**Decision Required**: Choose Path A or Path B to continue workflow

**Current Location**: `/Volumes/PSSD/Projects/公众号文章/产物/04_Material/2026-04-05_075240_ai/`

**Last Updated**: 2026-04-05 16:57
