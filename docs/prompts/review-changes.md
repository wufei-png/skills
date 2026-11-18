# 只读评审与意见核实

用于审查一段差异、测试、计划或文档，也可附上已有评审意见请 Agent 核实。

```text
请只读评审 <差异、测试范围或文档>，以 <目标和已确认契约> 为准。
[可选] 用 $review-tests 检查上述范围的测试能否发现实际缺陷。
[可选] 用 $improve-code-comments 审查上述范围的注释和 docstring。
沿受影响的调用或使用路径核对 <关注点>。
将确认的问题按影响排序，每条给出位置、触发条件、影响和修复方向。如附有评审意见，逐条核实问题是否成立且值得修复。未发现问题时，说明实际覆盖范围和仍需验证的行为。
```

Skill 说明见 [review-tests](../../skills/engineering/review-tests/SKILL.md) 和 [improve-code-comments](../../skills/engineering/improve-code-comments/SKILL.md)。
