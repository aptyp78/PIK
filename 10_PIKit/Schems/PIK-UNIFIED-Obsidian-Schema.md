---
type: artifact
id: PIK-UNIFIED-schema
title: "PIK Unified Methodology — схема для Obsidian"
version: "1.0.0"
status: "approved"
owner: "Knowledge Steward"
source_org: "PIK"
source_url: ""
source_date: "2025-09-06"
tags: ["PIK","SSOT","diagram","mermaid"]
links:
  related_frameworks: ["[[Platform Innovation Kit 5 0]]"]
  related_playbooks: ["[[Ecosystem Strategy Playbook]]","[[Obsidian SSOT Playbook]]"]
  related_canvases: ["[[PIK-SSOT.canvas]]","[[PBK-Obsidian-SSOT.canvas]]"]
  related_terms: ["[[Double Loop]]","[[Network Effects]]","[[Governance]]","[[SSOT]]"]
---

> Схема подготовлена в соответствии с доктриной Obsidian SSOT. Для импортирования — поместите файл в хранилище и откройте. fileciteturn2file0

# Unified Methodology Map

```mermaid
graph TB
  A[PIK 5 0 Unified Methodology Map]

  %% Upstream: Ecosystem Strategy
  subgraph Upstream Ecosystem Strategy
    ES0[Upstream Ecosystem Strategy]

    subgraph L1 Portfolio Level
      L1A[Ecosystems Portfolio Map]
      L1B[Portfolio strategies market expansion - integration - focus - role dominance]
    end

    subgraph L2 Market Level
      L2A[Ecosystem Journey Canvas]
      L2B[Functional Integration Map]
      L2C[Value pools and control points]
      L2D[Buy Build Partner Join]
      L2E[Viability checklist]
      L2E1[Fragmented demand]
      L2E2[Fragmented supply]
      L2E3[Matching]
      L2E4[Trust]
      L2E5[Supplier coordination]
      L2E6[Co innovation]
    end

    subgraph L3 Platform Level
      L3A[Platform Value Network]
      L3B[Platform Service Canvas]
      L3C[Network effects and trust]
    end

    subgraph Ecosystem Strategy Process 8 weeks
      P1[Needs]
      P2[Vision]
      P3[Offerings]
      P4[Ventures]
      P5[Initiate]
      P1 --> P2 --> P3 --> P4 --> P5
    end

    L1A --> L2A --> L3A
    L1B --> L2B
    L2C --> L2D
    L2E --> L2E1
    L2E --> L2E2
    L2E --> L2E3
    L2E --> L2E4
    L2E --> L2E5
    L2E --> L2E6
  end

  %% Core: Double Loop
  subgraph PIK Double Loop
    DL0[Double Loop]

    subgraph Discover and Launch
      DL1[Context]
      DL2[Need and Problem]
      DL3[Market]
      DL4[Solution]
      DL5[Minimal Viable Platform]
      DL6[Go to Market Strategy]
      DL7[Business Monetization and Market Opportunity]
      DL8[Governance]
      DL9[Team]
      DL10[Competition]
      DL11[Unfair Advantage]
      DL1 --> DL2 --> DL3 --> DL4 --> DL5 --> DL6 --> DL7 --> DL8 --> DL9 --> DL10 --> DL11
    end

    subgraph Growth and Scale
      GS1[Trust]
      GS2[Ecosystem]
      GS3[Communities]
      GS4[Interactions]
      GS5[Experience]
      GS6[Growth and Liquidity]
      GS7[Network Effects]
      GS8[Partnerships]
      GS9[Data]
      GS10[Infrastructure]
      GS11[Expansion Strategy]
      GS1 --> GS2 --> GS3 --> GS4 --> GS5 --> GS6 --> GS7 --> GS8 --> GS9 --> GS10 --> GS11
    end

    DL11 --> GS1
  end

  %% Perspectives crosswalk
  subgraph Perspectives
    Pm[Market]
    Ps[Solution]
    Pb[Business]
    Pc[Competencies]
  end

  %% Core Canvases
  subgraph Core Canvases
    C0[Core Canvases]
    C1[Platform Business Model Canvas]
    C2[Deep dive canvases]
    C3[Network Effects Reinforcement Engines]
    C4[Platform Growth Engine]
  end

  %% Sustainability
  subgraph Sustainability by Design
    S0[Sustainability by Design]
    S1[Ecosystem impact areas]
    S2[UN SDGs support]
    S3[Updated guides]
  end

  %% Advanced tools
  subgraph Advanced Tools
    AT0[Advanced Tools]
    AT1[Platform Value Stack]
    AT2[Business Case and Metrics]
    AT3[Trust and Governance]
    AT4[Data Flywheel]
    AT5[IT Architecture]
    AT6[Ecosystem Strategy Playbook]
  end

  %% Top level wiring
  A --> ES0
  A --> DL0
  A --> C0
  A --> S0
  A --> AT0

  %% Cross-links logic
  Pm --- DL3
  Ps --- DL4
  Pb --- DL7
  Pc --- DL9

  L3A --> DL4
  L3B --> DL5
  L3C --> GS7

  C1 --- DL7
  C2 --- DL5
  C3 --- GS7
  C4 --- GS6

  S1 --- DL1
  S2 --- DL7
  S3 --- GS1

  AT1 --- DL4
  AT2 --- DL7
  AT3 --- GS1
  AT4 --- GS9
  AT5 --- GS10
  AT6 --- L1A

  %% Feedback loops for reframing
  GS11 -.-> L2A
  GS9  -.-> L2C
  GS7  -.-> L1B
```
^diagram-unified

## Примечания
- Названия узлов совпадают с именами будущих заметок для простого связывания вручную через вики-ссылки.
- Рекомендуется завести MOC узлы для уровней L1 L2 L3 и для петли Double Loop.
- Для операционки используйте Canvas карты `PIK-SSOT.canvas` и `PBK-Obsidian-SSOT.canvas` рядом с этой схемой.
