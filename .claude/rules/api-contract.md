---
paths:
  - "apps/backend/routers/**"
  - "apps/backend/data_models/**"
  - "apps/backend/orchestrator/**"
  - "apps/backend/llm/**"
  - "apps/web/types/**"
  - "apps/web/lib/fastApiClient.ts"
  - "apps/web/lib/*Db.ts"
  - "apps/web/app/api/**"
  - "apps/web/app/actions/**"
---

# FastAPI ↔ Next.js contract

All endpoints live in `apps/backend/routers/chart.py` under `/v1/chart`. Next.js calls them
server-to-server through `apps/web/lib/fastApiClient.ts`. The wire types live in
`apps/web/types/api.ts`; chart shapes in `types/baziChart.ts` and `types/cyclesChart.ts`.

**Chinese keys end to end.** The frontend reads `data` with its Chinese keys. Map them to TypeScript
interfaces but never rename keys to camelCase. **A shape change updates the backend, the matching
`types/*.ts`, and this file in the same commit.**

## POST `/v1/chart/natal`
**Request (BirthInput):**
```python
class BirthInput(BaseModel):
    year: int                           # Gregorian year
    month: int                          # 1-12
    day: int                            # 1-31
    hour: int                           # 0-23 (wall-clock time)
    minute: int                         # 0-59
    gender: int                         # 1 = male, 0 = female
    latitude: float                     # Birth location (decimal degrees)
    longitude: float                    # Birth location (decimal degrees)
    use_solar_time_correction: bool     # Default True — apply TST conversion
```

**Response (NatalChartResponse):** `{data: Dict[str, Any], chart_key: str}` — `chart_key` is the
八字-based cache key (8 GanZhi letters + gender, from `astronomer_logic/bazi_key.py`), e.g.
`"bBdLeEgIM"`. It is identical for everyone with the same four pillars + gender. Top-level `data`:
```json
{
  "农历生日": "农历日期 (时辰)",
  "性别": "男 | 女",
  "生肖": "鼠 | 牛 | ... 猪",
  "生时节气": "节气名称",
  "四柱实体": {
    "年柱": { "天干": {...}, "地支": {...}, "藏干": {...}, "十二长生": {...}, "空亡": {...}, "纳音": {...} },
    "月柱": { ... }, "日柱": { ... }, "时柱": { ... }
  },
  "日主": { ... },
  "五行": { ... },
  "用神": { ... },
  "神煞": { ... },
  "胎命身": { "胎": "...", "命": "...", "身": "..." },
  "古籍文献": { ... },
  "作用": { ... },
  "古籍解读": { ... }
}
```
Ten gods, 根基强度 and 通根 sit inside the per-pillar `天干`/`地支`/`藏干` objects. `古籍解读` is the output
of the 三命通会 rule engine (`interaction_natal_chart.evaluate_rule`).

## POST `/v1/chart/cycles`
**Request (CyclesInput = BirthInput +):**
```python
class CyclesInput(BirthInput):
    da_yun_index: Optional[int]   # 0-9; when set, that decade's 流年 list is populated
```

**Response (CyclesResponse):** `{data: Dict[str, Any], chart_key: str}` where `data`:
```json
{
  "起运": { "顺逆": "顺推|逆推", "起运阳历": "...", "起运计岁": "...", "性别": "..." },
  "用神": { "强弱", "格局", "格局详情", "五神", "调候适用", "调候用神", "调候忌神", "调候喜五行", "调候忌五行",
           "喜用", "忌", "仇", "闲", "大运喜", "大运忌", "五行", "经典" },
  // 五神 = { 用神 (singular; "" iff 喜用 空), 喜神 (rest of 喜用), 忌神, 仇神, 闲神 } — additive
  //   presentation split of the sets; 综合/角色 stay authoritative. See yong_shen._select_yong_shen.
  // 五行[元素] = { 十神, 扶抑, 调候, 综合 (喜|忌|平), 角色 (喜用神|忌神|仇神|闲神), 备注 }
  "大运": [
    { "序号": 0, "阶段": "未行大运", "干支": "", "起始", "结束",
      "开始虚岁", "结束虚岁", "开始周岁", "结束周岁", "周期", "流年": [] },
    { "序号": 1, "干支": "丙戌", "起始": "1991-11-04 16:14:27", "结束": "2001-11-04 16:14:27",
      "开始虚岁": 7, "结束虚岁": 17, "开始周岁": 5, "结束周岁": 15, "周期": "7-17岁", ...,
      "运柱": { 天干/地支/藏干/十二长生/纳音/空亡/季节状态/制化 },
      "作用": { "关系总览": [...], "柱位动态": [...] },
      "神煞": [ { "名称", "来源", "解读" } ],
      "运势": { "评级": "喜运|平运|忌运", "依据": "...", "来源": "金不换|用神五行" },
      "五行动态": { "五行", "对日主", "引动" },
      // 五行[元素] = { 状态, 本命, 运基 (流年 only), 变化, 十神, 喜忌, 角色, 解读 }
      "古籍解读": { "纳音格局": [ { "逻辑名称", "来源", "结论", "证据", "现代解读"?, "依据"?, "标注"? } ], ... },
      // only groups with a match appear; {} = rules ran, none fired. See rules/bazi-cycles.md.
      "流年": [ { "年份", "起始", "结束", "交运年", "虚岁", "周岁", "干支", "生肖",
                 "运柱", "作用", "神煞",
                 "运势": { ..., "警示": ["岁运并临（重）：…"] },
                 "五行动态", "古籍解读",
                 "岁运": { "关系总览": [...], "特殊组合": [ {"名称","级别","说明"} ],
                          "大运态": "交战|入局|被合绊|受冲|常态", "大运态说明": "...",
                          "大运制约": [ {"类型","组合明细","原强度","本年强度","起因","说明"} ],
                          "警示": [...] },
                 "小运": { "干支", "运柱", "作用", "运势", "古籍解读" },  // pre-起运 years only
                 "太岁", "流月": [] } ] }
  ]
}
```
`岁运` is present on every 流年 EXCEPT the pre-起运 stub's (未行大运 — no decade to relate to).
`古籍解读` is present on every 大运 except the index-0 stub, and on every 流年.
`小运` is present ONLY on the 流年 of the pre-起运 stub (`da_yun_index=0`) — the hour pillar
stepped one 干支 per 虚岁 in the 大运's direction, scanned 1×4 against the natal chart.
`运势.警示` appears only when a 级别 "重" configuration fires.

**流年 are lazy:** default request returns all 10 大运 fully analysed with empty `流年` lists
(~62KB); pass `da_yun_index` to expand one decade (~157KB for its 11 流年, of which the 岁运 layer is
~14KB).

**Caching rule (critical):** cycle timing (起运) depends on the exact birth instant, which
`chart_key` deliberately excludes — **never cache cycle data under `chart_key`**. The response is
deterministic per (birth fields, lat/lon, TST flag, gender, da_yun_index); cache at the Next.js
layer per `profileId + daYunIndex` if needed. `chart_key` in the cycles response is for log
correlation only. The `/api/cycles` route handler reads birth data from the profile record
(owner-enforced), never from the client.

## POST `/v1/chart/insights` and `/v1/chart/insights/stream`
**Request (InsightsRequest):** `{data: <natal chart data>, section?: str}` — `section` is a key from
`llm/section_registry.py` (e.g. `personality`, `family`, `romance`, `career`, `wealth`); omit for
the full report. **Response (InsightsResponse):** `{sections: {key: payload}}` — narrative prose, or
a structured `{group: [{point, explanation}]}` object for sections that define categories. The
`/stream` variant streams one section. Provider is chosen by `active_provider` in
`config/llm_config.yaml`.

## Request headers
Next.js sends `X-Request-Id`, `X-Chart-Key`, `X-User-Id`, `X-Profile-Id`; `bind_log_context` in
`chart.py` binds them to log context vars (`apps/utils/logging.py`).

**Auth:** it also sends `Authorization: Bearer $FASTAPI_BEARER_TOKEN`, enforced router-wide by
`require_bearer_token` (`apps/backend/security.py`) — any new `/v1/chart/*` route inherits it.
Token set → 401 unless it matches (constant-time compare; auth runs before body validation).
Token unset → 503 on Cloud Run (`K_SERVICE` present), allowed with a warning locally. `/health`
stays unauthenticated for Cloud Run probes. The frontend maps 401/403 to a config error
(`lib/errors.ts`), never a user-facing auth prompt.

## Firestore (written by Next.js only)
| Collection | Key | Holds |
|---|---|---|
| `profiles` | `profileId` | Birth data + `userId` owner |
| `chartCache` | `chart_key` | Natal `data`, shared by every profile with the same 八字 + gender |
| `insightsCache` | `profileId` | Insight sections, regenerated per profile |

Chart creation (`app/api/chart/route.ts`) always calls `/natal` — the key is derived by the
backend, so the cache cannot be checked first — then writes `chartCache` and `profiles`. Insights
are not generated on create.

FastAPI errors reach the browser only through `lib/errors.ts` (`toClientError`); never forward raw
backend messages.
