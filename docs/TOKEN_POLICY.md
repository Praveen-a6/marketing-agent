# Token Policy & Cost Optimization

## Model Routing
| Task | Model |
|------|-------|
| Classification, FAQs | DeepSeek V4 Flash |
| Summaries, Drafts | DeepSeek V4 Flash |
| Complex planning | DeepSeek V4 Pro (approval) |
| Image gen | External API |

## Hard Limits
| Limit | Value |
|-------|-------|
| Max output (subtask) | 800 |
| Max output (draft) | 2000 |
| Max leads/batch | 10 |
| Max retries | 2 |
| Max time | 5 min |

## Budget Controls
| Threshold | Action |
|-----------|--------|
| 50% daily | Telegram warning |
| 80% daily | Stop non-essential |
| 100% daily | Disable scheduled jobs |

## Caching
- Cache research by domain for 7 days.
- Prefer `knowledge/` over LLM generation.

## Usage Logging
Log every call to `logs/usage.csv`:

```csv
timestamp,workflow,provider,model,input_tokens,output_tokens,cost_usd,status,error
Daily Report
Auto-generate daily report at 9:00 AM with usage summary and recommendations.
