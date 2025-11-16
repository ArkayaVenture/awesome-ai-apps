```mermaid
gantt
    title SRE Bot Delivery Roadmap (10 Sprints, 2 Weeks Each)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Release 1
    E1-Infra:done, e1, 2025-01-01, 28d
    E2-Platform:active, e2, after e1, 28d

    section Release 2
    E3-EKS-Addons: e3, after e2, 28d
    E4-Observability: e4, after e3, 28d

    section Release 3
    E6-Network: e6, after e4, 28d
    E7-Automation: e7, after e4, 42d

    section Release 4
    E5-Migration: e5, after e7, 28d

    section Release 5
    E8-Security/NFR: e8, after e4, 28d
    E9-Docs/Training: e9, after e8, 14d
    E10-Enablement: e10, after e9, 14d
```