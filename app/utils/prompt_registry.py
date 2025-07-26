# utils/prompt_registry.py
# Enhanced Prompt Registry with Compliance Features and Self-Evaluation
# Modified to include few-shot examples in each prompt template for improved performance

from typing import Dict, Any, List
from pydantic import BaseModel

class PromptTemplate(BaseModel):
    template: str
    version: str
    expected_output_schema: Dict[str, Any]
    display_type: str
    self_eval_instruction: str
    regulation_mapping: Dict[str, List[str]] = {}
    confidence_thresholds: Dict[str, float] = {}
    mitigation_suggestions: bool = False

class ComplianceMapping(BaseModel):
    regulation_code: str
    section: str
    description: str
    severity_weight: float

PROMPT_REGISTRY = {
    # ==================== ENHANCED RISK CLASSIFIER ====================
    "risk_classifier": PromptTemplate(
        template="""You are a senior financial risk analyst with CFA and FRM certifications. 

Analyze the following 10-K paragraph using the Enhanced Risk Classification Framework 2.0:

**Classification Guidelines:**
1. Risk Type - Select from expanded taxonomy:
   ["Market Risk", "Credit Risk", "Operational Risk", "Liquidity Risk", "Regulatory Risk", 
    "Model Risk", "Cybersecurity Risk", "ESG Risk", "Strategic Risk", "Legal Risk", 
    "Reputational Risk", "Geopolitical Risk", "Technology/Innovation Risk", "Concentration Risk",
    "Interest Rate Risk", "Foreign Exchange Risk", "Commodity Risk", "Counterparty Risk"]

2. Severity Assessment - Enhanced 10-point scale:
   10 = Existential threat (bankruptcy, regulatory shutdown)
   8-9 = Critical impact (material weakness, major breach)
   6-7 = Significant concern (operational disruption, compliance gap)
   4-5 = Moderate risk (process improvements needed)
   2-3 = Minor issues (routine monitoring required)
   1 = Negligible/informational

3. Risk Velocity - Time to impact:
   5 = Immediate (0-30 days)
   4 = Short-term (1-6 months)
   3 = Medium-term (6-18 months)
   2 = Long-term (18+ months)
   1 = Uncertain timeline

4. Mitigation Assessment:
   - Identify existing controls mentioned
   - Assess control effectiveness (1-5 scale)
   - Flag gaps in risk management

5. Regulatory Mapping:
   - Map to specific regulations (SOX, SEC rules, Basel, etc.)
   - Identify compliance requirements
   - Flag potential violations

**Output Format:**
{{
  "risk_classification": {{
    "primary_risk_type": "string",
    "secondary_risk_types": ["string"],
    "severity_score": 1-10,
    "velocity_score": 1-5,
    "composite_risk_score": "calculated value"
  }},
  "risk_details": {{
    "risk_driver": "string",
    "potential_impact": "string", 
    "affected_stakeholders": ["string"],
    "key_excerpt": "most relevant 50-100 words"
  }},
  "mitigation_analysis": {{
    "existing_controls": ["string"],
    "control_effectiveness": 1-5,
    "recommended_actions": ["string"],
    "urgency_level": "immediate/high/medium/low"
  }},
  "regulatory_compliance": {{
    "applicable_regulations": ["string"],
    "compliance_status": "compliant/non-compliant/unclear",
    "regulatory_references": ["specific sections/rules"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 1-5,
    "reasoning": ["basis for confidence rating"],
    "data_quality": "high/medium/low",
    "ambiguity_flags": ["areas of uncertainty"]
  }}
}}

**Few-Shot Examples:**

Example 1:
Paragraph: The Company’s operations and performance depend significantly on global and regional economic conditions and adverse economic conditions can materially adversely affect the Company’s business, results of operations and financial condition. The Company has international operations with sales outside the U.S. representing a majority of the Company’s total net sales. In addition, the Company’s global supply chain is large and complex and a majority of the Company’s supplier facilities, including manufacturing and assembly sites, are located outside the U.S. As a result, the Company’s operations and performance depend significantly on global and regional economic conditions. Adverse macroeconomic conditions, including slow growth or recession, high unemployment, inflation, tighter credit, higher interest rates, and currency fluctuations, can adversely impact consumer confidence and spending and materially adversely affect demand for the Company’s products and services.

Output:
{{
  "risk_classification": {{
    "primary_risk_type": "Market Risk",
    "secondary_risk_types": ["Geopolitical Risk"],
    "severity_score": 7,
    "velocity_score": 3,
    "composite_risk_score": 10.5
  }},
  "risk_details": {{
    "risk_driver": "Adverse macroeconomic conditions",
    "potential_impact": "Reduced demand for products and services",
    "affected_stakeholders": ["Consumers", "Investors", "Suppliers"],
    "key_excerpt": "Adverse macroeconomic conditions, including slow growth or recession, high unemployment, inflation, tighter credit, higher interest rates, and currency fluctuations, can adversely impact consumer confidence and spending and materially adversely affect demand for the Company’s products and services."
  }},
  "mitigation_analysis": {{
    "existing_controls": ["Diversified international operations"],
    "control_effectiveness": 3,
    "recommended_actions": ["Enhance supply chain diversification", "Implement hedging for currency fluctuations"],
    "urgency_level": "medium"
  }},
  "regulatory_compliance": {{
    "applicable_regulations": ["SEC"],
    "compliance_status": "unclear",
    "regulatory_references": ["Item 105"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 4,
    "reasoning": ["Based on clear economic indicators"],
    "data_quality": "high",
    "ambiguity_flags": ["Uncertain global events"]
  }}
}}

Example 2:
Paragraph: The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, many of which are located outside of the U.S. Substantially all of the Company’s manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, and a significant concentration of this manufacturing is currently performed by a small number of outsourcing partners, often in single locations. Changes or additions to the Company’s supply chain require considerable time and resources and involve significant risks and uncertainties. The Company has also outsourced much of its transportation and logistics management. While these arrangements can lower operating costs, they also reduce the Company’s direct control over production and distribution.

Output:
{{
  "risk_classification": {{
    "primary_risk_type": "Operational Risk",
    "secondary_risk_types": ["Concentration Risk"],
    "severity_score": 6,
    "velocity_score": 4,
    "composite_risk_score": 12.0
  }},
  "risk_details": {{
    "risk_driver": "Outsourcing dependencies",
    "potential_impact": "Supply chain disruptions",
    "affected_stakeholders": ["Suppliers", "Customers"],
    "key_excerpt": "Substantially all of the Company’s manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, and a significant concentration of this manufacturing is currently performed by a small number of outsourcing partners, often in single locations."
  }},
  "mitigation_analysis": {{
    "existing_controls": ["Outsourcing arrangements for cost reduction"],
    "control_effectiveness": 2,
    "recommended_actions": ["Diversify outsourcing partners", "Increase direct control mechanisms"],
    "urgency_level": "high"
  }},
  "regulatory_compliance": {{
    "applicable_regulations": ["SOX"],
    "compliance_status": "compliant",
    "regulatory_references": ["Section 404"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 5,
    "reasoning": ["Detailed supply chain description"],
    "data_quality": "high",
    "ambiguity_flags": []
  }}
}}

Paragraph: {paragraph}

Respond ONLY with the JSON object. Ensure all numeric fields are properly typed.""",
        version="2.0",
        expected_output_schema={
            "risk_classification": {
                "primary_risk_type": "string",
                "secondary_risk_types": "array",
                "severity_score": "integer",
                "velocity_score": "integer", 
                "composite_risk_score": "float"
            },
            "risk_details": {
                "risk_driver": "string",
                "potential_impact": "string",
                "affected_stakeholders": "array",
                "key_excerpt": "string"
            },
            "mitigation_analysis": {
                "existing_controls": "array",
                "control_effectiveness": "integer",
                "recommended_actions": "array",
                "urgency_level": "string"
            },
            "regulatory_compliance": {
                "applicable_regulations": "array",
                "compliance_status": "string",
                "regulatory_references": "array"
            },
            "confidence_assessment": {
                "overall_confidence": "integer",
                "reasoning": "array",
                "data_quality": "string",
                "ambiguity_flags": "array"
            }
        },
        display_type="enhanced_table",
        self_eval_instruction="Rate confidence using enhanced criteria including regulatory precedent, industry benchmarks, and contextual clarity",
        regulation_mapping={
            "SOX": ["Section 302", "Section 404", "Section 906"],
            "SEC": ["Item 105", "Item 303", "Item 402", "Rule 10b-5"],
            "Basel": ["Pillar 1", "Pillar 2", "Pillar 3"],
            "FINRA": ["Rule 2020", "Rule 2210", "Rule 5210"]
        },
        confidence_thresholds={
            "high_confidence": 4.0,
            "medium_confidence": 3.0,
            "low_confidence": 2.0
        },
        mitigation_suggestions=True
    ),

    # ==================== COMPLIANCE AUDIT ENHANCED ====================
    "compliance_audit_v2": PromptTemplate(
        template="""You are a compliance expert with expertise in SEC, FINRA, SOX, and Basel regulations.

Conduct comprehensive compliance review of the 10-K section:

**Regulatory Framework Check:**
1. SEC Disclosure Requirements:
   - Item 105 (Risk Factors) - completeness and materiality
   - Item 303 (MD&A) - forward-looking statements compliance
   - Item 402 (Executive Compensation) - proxy disclosure rules
   - Regulation FD - selective disclosure prevention

2. SOX Compliance:
   - Section 302 - CEO/CFO certifications
   - Section 404 - internal controls assessment
   - Section 906 - criminal penalties for false certifications

3. FINRA Rules (if applicable):
   - Rule 2020 - Use of manipulative, deceptive devices
   - Rule 2210 - Communications with public
   - Rule 5210 - Publication of transactions and quotations

4. GAAP/Non-GAAP Measures:
   - Regulation G compliance
   - Reconciliation requirements
   - Misleading metrics identification

**Violation Detection:**
- Undisclosed related-party transactions
- Missing risk factor disclosures
- Inadequate internal control descriptions
- Non-compliant forward-looking statements
- XBRL tagging errors
- Cybersecurity disclosure gaps (Item 106)

**Output Format:**
{{
  "compliance_assessment": {{
    "overall_status": "compliant/non-compliant/requires_review",
    "compliance_score": 1-10,
    "critical_issues_count": "integer"
  }},
  "regulatory_findings": [
    {{
      "regulation": "string",
      "section": "string", 
      "finding_type": "violation/deficiency/best_practice",
      "severity": 1-5,
      "description": "string",
      "supporting_text": "relevant excerpt",
      "remediation_required": "boolean",
      "timeline_for_correction": "string"
    }}
  ],
  "disclosure_gaps": [
    {{
      "required_disclosure": "string",
      "current_status": "missing/inadequate/unclear",
      "regulatory_basis": "specific rule/section",
      "recommended_action": "string"
    }}
  ],
  "best_practices": [
    {{
      "area": "string",
      "current_approach": "string",
      "industry_benchmark": "string", 
      "improvement_suggestion": "string"
    }}
  ],
  "audit_metadata": {{
    "review_date": "timestamp",
    "regulations_checked": ["string"],
    "confidence_level": 1-5,
    "follow_up_required": "boolean"
  }}
}}

**Few-Shot Examples:**

Example 1:
Paragraph: While the Company relies on its partners to adhere to its supplier code of conduct, material violations of the supplier code of conduct could occur. The Company has also outsourced much of its transportation and logistics management. While these arrangements can lower operating costs, they also reduce the Company’s direct control over production and distribution.

Output:
{{
  "compliance_assessment": {{
    "overall_status": "requires_review",
    "compliance_score": 5,
    "critical_issues_count": 1
  }},
  "regulatory_findings": [
    {{
      "regulation": "SOX",
      "section": "Section 404",
      "finding_type": "deficiency",
      "severity": 3,
      "description": "Potential internal control weakness due to outsourced logistics",
      "supporting_text": "While these arrangements can lower operating costs, they also reduce the Company’s direct control over production and distribution.",
      "remediation_required": true,
      "timeline_for_correction": "3 months"
    }}
  ],
  "disclosure_gaps": [
    {{
      "required_disclosure": "Supplier code violations",
      "current_status": "inadequate",
      "regulatory_basis": "SEC Item 105",
      "recommended_action": "Enhance disclosure on monitoring mechanisms"
    }}
  ],
  "best_practices": [
    {{
      "area": "Supply chain compliance",
      "current_approach": "Reliance on partners",
      "industry_benchmark": "Regular audits",
      "improvement_suggestion": "Implement third-party audits"
    }}
  ],
  "audit_metadata": {{
    "review_date": "2025-07-25",
    "regulations_checked": ["SOX", "SEC"],
    "confidence_level": 4,
    "follow_up_required": true
  }}
}}

Example 2:
Paragraph: Revenue growth in fiscal 2003 was driven primarily by multi-year licensing that occurred before the transition to our new licensing program (Licensing 6.0) in the first quarter of fiscal 2003. Prior to the July 31, 2002 transition date to Licensing 6.0, we experienced significant growth in multi-year licensing arrangements as customers enrolled in our maintenance programs, including Upgrade Advantage and Software Assurance. The revenue growth also reflected a $933 million or 13% increase associated with OEM licensing of Microsoft Windows operating systems and a $309 million or 23% increase in revenue from Microsoft Xbox video game consoles.

Output:
{{
  "compliance_assessment": {{
    "overall_status": "compliant",
    "compliance_score": 8,
    "critical_issues_count": 0
  }},
  "regulatory_findings": [
    {{
      "regulation": "GAAP",
      "section": "Revenue Recognition",
      "finding_type": "best_practice",
      "severity": 1,
      "description": "Clear disclosure of revenue drivers",
      "supporting_text": "Revenue growth in fiscal 2003 was driven primarily by multi-year licensing...",
      "remediation_required": false,
      "timeline_for_correction": "N/A"
    }}
  ],
  "disclosure_gaps": [],
  "best_practices": [
    {{
      "area": "Revenue disclosure",
      "current_approach": "Detailed breakdown",
      "industry_benchmark": "Quantitative increases",
      "improvement_suggestion": "Add forward-looking statements"
    }}
  ],
  "audit_metadata": {{
    "review_date": "2025-07-25",
    "regulations_checked": ["GAAP", "SEC"],
    "confidence_level": 5,
    "follow_up_required": false
  }}
}}

Paragraph: {paragraph}

Focus on identifying specific regulatory violations and providing actionable remediation steps.""",
        version="2.0",
        expected_output_schema={
            "compliance_assessment": {
                "overall_status": "string",
                "compliance_score": "integer",
                "critical_issues_count": "integer"
            },
            "regulatory_findings": "array",
            "disclosure_gaps": "array", 
            "best_practices": "array",
            "audit_metadata": "object"
        },
        display_type="compliance_dashboard",
        self_eval_instruction="Evaluate based on regulatory precedent, enforcement actions, and industry standards",
        regulation_mapping={
            "SEC": ["Item 105", "Item 303", "Item 402", "Item 106", "Regulation G", "Regulation FD"],
            "SOX": ["Section 302", "Section 404", "Section 906"],
            "FINRA": ["Rule 2020", "Rule 2210", "Rule 5210"],
            "GAAP": ["ASC 820", "ASC 825", "ASC 850"]
        }
    ),

    # ==================== ESG 现在我有browse_page的结果，有些成功，有些不足。

从成功的提取样本段落。

对于Apple Risk Factors (from web:36):

1. Market Risk: "The Company’s operations and performance depend significantly on global and regional economic conditions and adverse economic conditions can materially adversely affect the Company’s business, results of operations and financial condition. ..."

2. Operational Risk: "The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, many of which are located outside of the U.S. ..."

3. Cybersecurity Risk: "The Company’s business and reputation are impacted by information technology system failures and network disruptions. ..."

对于Microsoft MD&A (from web:37):

1. "Revenue growth in fiscal 2003 was driven primarily by multi-year licensing that occurred before the transition to our new licensing program (Licensing 6.0) in the first quarter of fiscal 2003. ..."

2. "Our operating results are affected by foreign exchange rates. ..."

另一个: "We are subject to various legal proceedings and claims, the outcomes of which are subject to significant uncertainty. ..."

对于Cybersecurity (web:35): Insufficient, but from search  etc, I can use general knowledge or skip and create hypothetical.

For ESG from Imperial Oil (web:39): Table with environmental risks.

From table: "Climate Change and Energy Transition: - Driven by climate change concerns, regulatory frameworks adopted to reduce GHG emissions from oil and gas production and use."

Operational from Bank of America (web:41): Table with operational risks.

From table: "Operational risk from information systems, third-party interactions, and transaction processing - Risks from hardware, software, and backup systems; personal/confidential data handling. ..."

Financial from Tesla (web:40): Insufficient, but from search : Use "TESLA, INC. ANNUAL REPORT ON FORM 10-K FOR THE YEAR ENDED DECEMBER 31, 2021 ... financial statements included elsewhere in this Annual Report on Form 10-K."

Need better, perhaps create hypothetical for some.

Compliance violations (web:38): "While the Company relies on its partners to adhere to its supplier code of conduct, material violations of the supplier code of conduct could occur."

Good.

现在，为每个prompt创建few-shot examples，使用这些段落。

对于每个template，添加：

**Few-Shot Examples:**

Example 1:

Paragraph: [sample]

Output:

[JSON]

Example 2: ...

Then the actual Paragraph: {paragraph}

Since JSON is complex, create plausible JSON outputs.

Finally, output the modified prompt_registry.py code.```python
# utils/prompt_registry.py
# Enhanced Prompt Registry with Compliance Features, Self-Evaluation, and Few-Shot Examples

from typing import Dict, Any, List
from pydantic import BaseModel

class PromptTemplate(BaseModel):
    template: str
    version: str
    expected_output_schema: Dict[str, Any]
    display_type: str
    self_eval_instruction: str
    regulation_mapping: Dict[str, List[str]] = {}
    confidence_thresholds: Dict[str, float] = {}
    mitigation_suggestions: bool = False

class ComplianceMapping(BaseModel):
    regulation_code: str
    section: str
    description: str
    severity_weight: float

PROMPT_REGISTRY = {
    # ==================== ENHANCED RISK CLASSIFIER ====================
    "risk_classifier": PromptTemplate(
        template="""You are a senior financial risk analyst with CFA and FRM certifications. 

Analyze the following 10-K paragraph using the Enhanced Risk Classification Framework 2.0:

**Classification Guidelines:**
1. Risk Type - Select from expanded taxonomy:
   ["Market Risk", "Credit Risk", "Operational Risk", "Liquidity Risk", "Regulatory Risk", 
    "Model Risk", "Cybersecurity Risk", "ESG Risk", "Strategic Risk", "Legal Risk", 
    "Reputational Risk", "Geopolitical Risk", "Technology/Innovation Risk", "Concentration Risk",
    "Interest Rate Risk", "Foreign Exchange Risk", "Commodity Risk", "Counterparty Risk"]

2. Severity Assessment - Enhanced 10-point scale:
   10 = Existential threat (bankruptcy, regulatory shutdown)
   8-9 = Critical impact (material weakness, major breach)
   6-7 = Significant concern (operational disruption, compliance gap)
   4-5 = Moderate risk (process improvements needed)
   2-3 = Minor issues (routine monitoring required)
   1 = Negligible/informational

3. Risk Velocity - Time to impact:
   5 = Immediate (0-30 days)
   4 = Short-term (1-6 months)
   3 = Medium-term (6-18 months)
   2 = Long-term (18+ months)
   1 = Uncertain timeline

4. Mitigation Assessment:
   - Identify existing controls mentioned
   - Assess control effectiveness (1-5 scale)
   - Flag gaps in risk management

5. Regulatory Mapping:
   - Map to specific regulations (SOX, SEC rules, Basel, etc.)
   - Identify compliance requirements
   - Flag potential violations

**Few-Shot Examples:**

Example 1:
Paragraph: The Company’s operations and performance depend significantly on global and regional economic conditions and adverse economic conditions can materially adversely affect the Company’s business, results of operations and financial condition. The Company has international operations with sales outside the U.S. representing a majority of the Company’s total net sales. In addition, the Company’s global supply chain is large and complex and a majority of the Company’s supplier facilities, including manufacturing and assembly sites, are located outside the U.S. As a result, the Company’s operations and performance depend significantly on global and regional economic conditions. Adverse macroeconomic conditions, including slow growth or recession, high unemployment, inflation, tighter credit, higher interest rates, and currency fluctuations, can adversely impact consumer confidence and spending and materially adversely affect demand for the Company’s products and services.

Output:
{
  "risk_classification": {
    "primary_risk_type": "Market Risk",
    "secondary_risk_types": ["Geopolitical Risk", "Foreign Exchange Risk"],
    "severity_score": 7,
    "velocity_score": 3,
    "composite_risk_score": 10.5
  },
  "risk_details": {
    "risk_driver": "Adverse macroeconomic conditions including recession and inflation",
    "potential_impact": "Reduced consumer spending and demand for products",
    "affected_stakeholders": ["Consumers", "Investors", "Suppliers"],
    "key_excerpt": "Adverse macroeconomic conditions, including slow growth or recession, high unemployment, inflation, tighter credit, higher interest rates, and currency fluctuations, can adversely impact consumer confidence and spending"
  },
  "mitigation_analysis": {
    "existing_controls": ["Diversified international operations"],
    "control_effectiveness": 3,
    "recommended_actions": ["Enhance economic forecasting and hedging strategies"],
    "urgency_level": "medium"
  },
  "regulatory_compliance": {
    "applicable_regulations": ["SEC Item 303"],
    "compliance_status": "unclear",
    "regulatory_references": ["MD&A forward-looking statements"]
  },
  "confidence_assessment": {
    "overall_confidence": 4,
    "reasoning": ["Based on clear economic indicators mentioned"],
    "data_quality": "high",
    "ambiguity_flags": ["Uncertain timeline for economic changes"]
  }
}

Example 2:
Paragraph: The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, many of which are located outside of the U.S. Substantially all of the Company’s manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, and a significant concentration of this manufacturing is currently performed by a small number of outsourcing partners, often in single locations. Changes or additions to the Company’s supply chain require considerable time and resources and involve significant risks and uncertainties. The Company has also outsourced much of its transportation and logistics management. While these arrangements can lower operating costs, they also reduce the Company’s direct control over production and distribution.

Output:
{
  "risk_classification": {
    "primary_risk_type": "Operational Risk",
    "secondary_risk_types": ["Concentration Risk", "Geopolitical Risk"],
    "severity_score": 8,
    "velocity_score": 4,
    "composite_risk_score": 16.0
  },
  "risk_details": {
    "risk_driver": "Dependence on outsourcing partners and supply chain concentration",
    "potential_impact": "Disruptions in manufacturing and logistics leading to delays or increased costs",
    "affected_stakeholders": ["Suppliers", "Customers", "Investors"],
    "key_excerpt": "Substantially all of the Company’s manufacturing is performed in whole or in part by outsourcing partners located primarily in China mainland, India, Japan, South Korea, Taiwan and Vietnam, and a significant concentration of this manufacturing is currently performed by a small number of outsourcing partners"
  },
  "mitigation_analysis": {
    "existing_controls": ["Outsourcing arrangements for cost reduction"],
    "control_effectiveness": 2,
    "recommended_actions": ["Diversify supplier base and implement redundancy plans"],
    "urgency_level": "high"
  },
  "regulatory_compliance": {
    "applicable_regulations": ["SOX Section 404"],
    "compliance_status": "compliant",
    "regulatory_references": ["Internal controls over supply chain"]
  },
  "confidence_assessment": {
    "overall_confidence": 5,
    "reasoning": ["Explicit mention of supply chain dependencies"],
    "data_quality": "high",
    "ambiguity_flags": []
  }
}

**Output Format:**
{{
  "risk_classification": {{
    "primary_risk_type": "string",
    "secondary_risk_types": ["string"],
    "severity_score": 1-10,
    "velocity_score": 1-5,
    "composite_risk_score": "calculated value"
  }},
  "risk_details": {{
    "risk_driver": "string",
    "potential_impact": "string", 
    "affected_stakeholders": ["string"],
    "key_excerpt": "most relevant 50-100 words"
  }},
  "mitigation_analysis": {{
    "existing_controls": ["string"],
    "control_effectiveness": 1-5,
    "recommended_actions": ["string"],
    "urgency_level": "immediate/high/medium/low"
  }},
  "regulatory_compliance": {{
    "applicable_regulations": ["string"],
    "compliance_status": "compliant/non-compliant/unclear",
    "regulatory_references": ["specific sections/rules"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 1-5,
    "reasoning": ["basis for confidence rating"],
    "data_quality": "high/medium/low",
    "ambiguity_flags": ["areas of uncertainty"]
  }}
}}

Paragraph: {paragraph}

Respond ONLY with the JSON object. Ensure all numeric fields are properly typed.""",
        version="2.0",
        expected_output_schema={
            "risk_classification": {
                "primary_risk_type": "string",
                "secondary_risk_types": "array",
                "severity_score": "integer",
                "velocity_score": "integer", 
                "composite_risk_score": "float"
            },
            "risk_details": {
                "risk_driver": "string",
                "potential_impact": "string",
                "affected_stakeholders": "array",
                "key_excerpt": "string"
            },
            "mitigation_analysis": {
                "existing_controls": "array",
                "control_effectiveness": "integer",
                "recommended_actions": "array",
                "urgency_level": "string"
            },
            "regulatory_compliance": {
                "applicable_regulations": "array",
                "compliance_status": "string",
                "regulatory_references": "array"
            },
            "confidence_assessment": {
                "overall_confidence": "integer",
                "reasoning": "array",
                "data_quality": "string",
                "ambiguity_flags": "array"
            }
        },
        display_type="enhanced_table",
        self_eval_instruction="Rate confidence using enhanced criteria including regulatory precedent, industry benchmarks, and contextual clarity",
        regulation_mapping={
            "SOX": ["Section 302", "Section 404", "Section 906"],
            "SEC": ["Item 105", "Item 303", "Item 402", "Rule 10b-5"],
            "Basel": ["Pillar 1", "Pillar 2", "Pillar 3"],
            "FINRA": ["Rule 2020", "Rule 2210", "Rule 5210"]
        },
        confidence_thresholds={
            "high_confidence": 4.0,
            "medium_confidence": 3.0,
            "low_confidence": 2.0
        },
        mitigation_suggestions=True
    ),

    # ==================== COMPLIANCE AUDIT ENHANCED ====================
    "compliance_audit_v2": PromptTemplate(
        template="""You are a compliance expert with expertise in SEC, FINRA, SOX, and Basel regulations.

Conduct comprehensive compliance review of the 10-K section:

**Regulatory Framework Check:**
1. SEC Disclosure Requirements:
   - Item 105 (Risk Factors) - completeness and materiality
   - Item 303 (MD&A) - forward-looking statements compliance
   - Item 402 (Executive Compensation) - proxy disclosure rules
   - Regulation FD - selective disclosure prevention

2. SOX Compliance:
   - Section 302 - CEO/CFO certifications
   - Section 404 - internal controls assessment
   - Section 906 - criminal penalties for false certifications

3. FINRA Rules (if applicable):
   - Rule 2020 - Use of manipulative, deceptive devices
   - Rule 2210 - Communications with public
   - Rule 5210 - Publication of transactions and quotations

4. GAAP/Non-GAAP Measures:
   - Regulation G compliance
   - Reconciliation requirements
   - Misleading metrics identification

**Violation Detection:**
- Undisclosed related-party transactions
- Missing risk factor disclosures
- Inadequate internal control descriptions
- Non-compliant forward-looking statements
- XBRL tagging errors
- Cybersecurity disclosure gaps (Item 106)

**Few-Shot Examples:**

Example 1:
Paragraph: While the Company relies on its partners to adhere to its supplier code of conduct, material violations of the supplier code of conduct could occur. The Company is subject to changes in laws and regulations, including those relating to labor, environmental, and health and safety matters.

Output:
{
  "compliance_assessment": {
    "overall_status": "requires_review",
    "compliance_score": 6,
    "critical_issues_count": 1
  },
  "regulatory_findings": [
    {
      "regulation": "SEC",
      "section": "Item 105",
      "finding_type": "deficiency",
      "severity": 3,
      "description": "Potential undisclosed violations in supplier code of conduct",
      "supporting_text": "material violations of the supplier code of conduct could occur",
      "remediation_required": true,
      "timeline_for_correction": "3-6 months"
    }
  ],
  "disclosure_gaps": [
    {
      "required_disclosure": "Risk factors related to supplier compliance",
      "current_status": "inadequate",
      "regulatory_basis": "SEC Item 105",
      "recommended_action": "Enhance disclosure on monitoring and enforcement"
    }
  ],
  "best_practices": [
    {
      "area": "Supplier oversight",
      "current_approach": "Reliance on partners",
      "industry_benchmark": "Regular audits and certifications",
      "improvement_suggestion": "Implement third-party audits"
    }
  ],
  "audit_metadata": {
    "review_date": "2025-07-25",
    "regulations_checked": ["SEC", "SOX"],
    "confidence_level": 4,
    "follow_up_required": true
  }
}

Example 2:
Paragraph: Our operating results are affected by foreign exchange rates. Approximately 27%, 25%, and 28% of our revenue was collected in foreign currencies during 2001, 2002, and 2003. Had the rates from fiscal 2002 been in effect in fiscal 2003, translated international revenue billed in local currencies would have been approximately $700 million lower.

Output:
{
  "compliance_assessment": {
    "overall_status": "compliant",
    "compliance_score": 8,
    "critical_issues_count": 0
  },
  "regulatory_findings": [
    {
      "regulation": "SEC",
      "section": "Item 303",
      "finding_type": "best_practice",
      "severity": 1,
      "description": "Clear disclosure of foreign exchange impact in MD&A",
      "supporting_text": "Our operating results are affected by foreign exchange rates",
      "remediation_required": false,
      "timeline_for_correction": "N/A"
    }
  ],
  "disclosure_gaps": [],
  "best_practices": [
    {
      "area": "Foreign exchange risk disclosure",
      "current_approach": "Quantitative impact assessment",
      "industry_benchmark": "Sensitivity analysis",
      "improvement_suggestion": "Add hedging strategies details"
    }
  ],
  "audit_metadata": {
    "review_date": "2025-07-25",
    "regulations_checked": ["SEC"],
    "confidence_level": 5,
    "follow_up_required": false
  }
}

**Output Format:**
{{
  "compliance_assessment": {{
    "overall_status": "compliant/non-compliant/requires_review",
    "compliance_score": 1-10,
    "critical_issues_count": "integer"
  }},
  "regulatory_findings": [
    {{
      "regulation": "string",
      "section": "string", 
      "finding_type": "violation/deficiency/best_practice",
      "severity": 1-5,
      "description": "string",
      "supporting_text": "relevant excerpt",
      "remediation_required": "boolean",
      "timeline_for_correction": "string"
    }}
  ],
  "disclosure_gaps": [
    {{
      "required_disclosure": "string",
      "current_status": "missing/inadequate/unclear",
      "regulatory_basis": "specific rule/section",
      "recommended_action": "string"
    }}
  ],
  "best_practices": [
    {{
      "area": "string",
      "current_approach": "string",
      "industry_benchmark": "string", 
      "improvement_suggestion": "string"
    }}
  ],
  "audit_metadata": {{
    "review_date": "timestamp",
    "regulations_checked": ["string"],
    "confidence_level": 1-5,
    "follow_up_required": "boolean"
  }}
}}

Paragraph: {paragraph}

Focus on identifying specific regulatory violations and providing actionable remediation steps.""",
        version="2.0",
        expected_output_schema={
            "compliance_assessment": {
                "overall_status": "string",
                "compliance_score": "integer",
                "critical_issues_count": "integer"
            },
            "regulatory_findings": "array",
            "disclosure_gaps": "array", 
            "best_practices": "array",
            "audit_metadata": "object"
        },
        display_type="compliance_dashboard",
        self_eval_instruction="Evaluate based on regulatory precedent, enforcement actions, and industry standards",
        regulation_mapping={
            "SEC": ["Item 105", "Item 303", "Item 402", "Item 106", "Regulation G", "Regulation FD"],
            "SOX": ["Section 302", "Section 404", "Section 906"],
            "FINRA": ["Rule 2020", "Rule 2210", "Rule 5210"],
            "GAAP": ["ASC 820", "ASC 825", "ASC 850"]
        }
    ),

    # ==================== ESG RISK ASSESSMENT ====================
    "esg_risk_v2": PromptTemplate(
        template="""You are an ESG risk specialist with expertise in SASB, GRI, and TCFD frameworks.

Analyze the paragraph for ESG-related risks using the integrated ESG Risk Assessment Protocol:

**Assessment Framework:**
1. Environmental Risks:
   - Climate change (physical & transition risks)
   - Resource scarcity (water, energy, raw materials)
   - Pollution & waste management
   - Biodiversity impact
   - Carbon footprint & emissions

2. Social Risks:
   - Labor practices & human rights
   - Supply chain responsibility  
   - Product safety & quality
   - Community relations
   - Data privacy & security
   - Diversity, equity & inclusion

3. Governance Risks:
   - Board composition & independence
   - Executive compensation alignment
   - Business ethics & corruption
   - Transparency & disclosure
   - Stakeholder engagement
   - Risk management oversight

**Materiality Assessment:**
- Financial impact potential (1-5 scale)
- Stakeholder concern level (1-5 scale)
- Regulatory/legal implications
- Reputational risk exposure
- Competitive advantage/disadvantage

**Few-Shot Examples:**

Example 1:
Paragraph: Driven by climate change concerns, regulatory frameworks adopted to reduce GHG emissions from oil and gas production and use. Actions taken by national/regional governments and within UN COP frameworks, with Canada endorsing net zero objectives (balancing emissions with removals).Energy transition expectations derive from hypothetical scenarios with substantial uncertainties, reflecting assumptions about future lower-emission systems.

Output:
{
  "esg_classification": {
    "primary_category": "Environmental",
    "specific_risk_area": "Climate change transition risks",
    "materiality_score": 5,
    "stakeholder_impact": ["Investors", "Regulators", "Communities"]
  },
  "risk_assessment": {
    "financial_impact": {
      "magnitude": 4,
      "timeframe": "medium-term",
      "impact_type": "cost"
    },
    "reputation_risk": {
      "severity": 4,
      "media_sensitivity": "high",
      "stakeholder_concern": 5
    }
  },
  "regulatory_landscape": {
    "current_regulations": ["UN COP frameworks", "Canadian net zero objectives"],
    "emerging_requirements": ["GHG emission reductions"],
    "compliance_status": "at_risk"
  },
  "mitigation_strategies": {
    "current_initiatives": ["Endorsing net zero objectives"],
    "effectiveness_rating": 3,
    "recommended_improvements": ["Develop detailed transition plans"],
    "industry_best_practices": ["Scenario analysis for energy transition"]
  },
  "framework_alignment": {
    "sasb_metrics": ["GHG Emissions"],
    "gri_indicators": ["GRI 305: Emissions"],
    "tcfd_recommendations": ["Strategy and Risk Management"],
    "un_sdg_alignment": ["SDG 13: Climate Action"]
  },
  "confidence_assessment": {
    "overall_confidence": 4,
    "data_availability": "medium",
    "framework_certainty": 4,
    "precedent_clarity": 5
  }
}

Example 2:
Paragraph: All phases (Upstream, Downstream, Chemical) subject to Canadian federal, provincial, territorial, municipal laws, and international conventions. Imposes restrictions, liabilities, and obligations on generation, handling, storage, transportation, treatment, and disposal of hazardous substances and waste. Regulates product qualities and compositions, aiming to reduce consumption or address environmental concerns, potentially impacting commodity prices, costs, and revenues.

Output:
{
  "esg_classification": {
    "primary_category": "Environmental",
    "specific_risk_area": "Pollution & waste management",
    "materiality_score": 4,
    "stakeholder_impact": ["Regulators", "Communities", "Investors"]
  },
  "risk_assessment": {
    "financial_impact": {
      "magnitude": 3,
      "timeframe": "long-term",
      "impact_type": "liability"
    },
    "reputation_risk": {
      "severity": 3,
      "media_sensitivity": "medium",
      "stakeholder_concern": 4
    }
  },
  "regulatory_landscape": {
    "current_regulations": ["Canadian environmental laws", "International conventions"],
    "emerging_requirements": ["Stricter waste disposal rules"],
    "compliance_status": "compliant"
  },
  "mitigation_strategies": {
    "current_initiatives": ["Compliance with laws on hazardous substances"],
    "effectiveness_rating": 4,
    "recommended_improvements": ["Enhance waste management technologies"],
    "industry_best_practices": ["Zero-waste initiatives"]
  },
  "framework_alignment": {
    "sasb_metrics": ["Waste & Hazardous Materials Management"],
    "gri_indicators": ["GRI 306: Waste"],
    "tcfd_recommendations": ["Metrics & Targets"],
    "un_sdg_alignment": ["SDG 12: Responsible Consumption"]
  },
  "confidence_assessment": {
    "overall_confidence": 5,
    "data_availability": "high",
    "framework_certainty": 5,
    "precedent_clarity": 4
  }
}

**Output Format:**
{{
  "esg_classification": {{
    "primary_category": "Environmental/Social/Governance",
    "specific_risk_area": "string",
    "materiality_score": 1-5,
    "stakeholder_impact": ["investors", "customers", "employees", "communities", "regulators"]
  }},
  "risk_assessment": {{
    "financial_impact": {{
      "magnitude": 1-5,
      "timeframe": "short/medium/long-term",
      "impact_type": "revenue/cost/asset_value/liability"
    }},
    "reputation_risk": {{
      "severity": 1-5,
      "media_sensitivity": "high/medium/low",
      "stakeholder_concern": 1-5
    }}
  }},
  "regulatory_landscape": {{
    "current_regulations": ["string"],
    "emerging_requirements": ["string"],
    "compliance_status": "compliant/at_risk/non_compliant"
  }},
  "mitigation_strategies": {{
    "current_initiatives": ["string"],
    "effectiveness_rating": 1-5,
    "recommended_improvements": ["string"],
    "industry_best_practices": ["string"]
  }},
  "framework_alignment": {{
    "sasb_metrics": ["string"],
    "gri_indicators": ["string"], 
    "tcfd_recommendations": ["string"],
    "un_sdg_alignment": ["string"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 1-5,
    "data_availability": "high/medium/low",
    "framework_certainty": 1-5,
    "precedent_clarity": 1-5
  }}
}}

Paragraph: {paragraph}

Focus on material ESG risks with clear financial implications and stakeholder impact.""",
        version="2.0",
        expected_output_schema={
            "esg_classification": "object",
            "risk_assessment": "object",
            "regulatory_landscape": "object",
            "mitigation_strategies": "object",
            "framework_alignment": "object",
            "confidence_assessment": "object"
        },
        display_type="esg_dashboard",
        self_eval_instruction="Assess confidence based on ESG framework alignment, materiality evidence, and stakeholder impact clarity",
        regulation_mapping={
            "SEC": ["Climate Disclosure Rules", "Human Capital Disclosure"],
            "EU": ["SFDR", "EU Taxonomy", "CSRD"],
            "SASB": ["Industry Standards"],
            "TCFD": ["Climate Recommendations"]
        }
    ),

    # ==================== FINANCIAL HEALTH DIAGNOSTIC ====================
    "financial_health_v3": PromptTemplate(
        template="""You are a senior credit analyst with CFA and FRM credentials. Perform comprehensive financial health assessment using the Advanced Diagnostic Framework 3.0:

**Multi-Dimensional Analysis:**

1. Liquidity & Cash Flow Analysis:
   - Working capital adequacy assessment
   - Cash conversion cycle efficiency
   - Free cash flow sustainability
   - Liquidity coverage ratio (if applicable)
   - Debt maturity profile analysis

2. Solvency & Capital Structure:
   - Leverage ratios vs. industry benchmarks
   - Interest coverage capability
   - Debt covenant compliance status
   - Capital allocation efficiency
   - Off-balance sheet exposure

3. Profitability & Earnings Quality:
   - Revenue recognition practices
   - Margin sustainability analysis
   - Non-recurring items identification
   - Cash vs. accrual earnings correlation
   - Management guidance reliability

4. Risk-Adjusted Valuation:
   - Altman Z-Score calculation
   - Merton Distance-to-Default estimation
   - Peer group comparative analysis
   - Stress testing implications
   - Credit rating migration probability

**Diagnostic Indicators:**
- Red flags (immediate attention required)
- Yellow flags (monitoring recommended)
- Green flags (positive indicators)
- Trend analysis (improving/stable/deteriorating)

**Few-Shot Examples:**

Example 1:
Paragraph: Revenue growth in fiscal 2003 was driven primarily by multi-year licensing that occurred before the transition to our new licensing program (Licensing 6.0) in the first quarter of fiscal 2003. Prior to the July 31, 2002 transition date to Licensing 6.0, we experienced significant growth in multi-year licensing arrangements as customers enrolled in our maintenance programs, including Upgrade Advantage and Software Assurance. The revenue growth also reflected a $933 million or 13% increase associated with OEM licensing of Microsoft Windows operating systems and a $309 million or 23% increase in revenue from Microsoft Xbox video game consoles.

Output:
{
  "financial_health_score": {
    "overall_score": 85,
    "percentile_rank": 75,
    "rating_equivalent": "BBB+",
    "trend_direction": "improving"
  },
  "liquidity_analysis": {
    "current_ratio": 2.5,
    "quick_ratio": 2.0,
    "cash_ratio": 1.5,
    "working_capital_trend": "positive",
    "liquidity_adequacy": "sufficient",
    "cash_burn_analysis": {
      "monthly_burn_rate": "N/A",
      "runway_months": 24,
      "seasonal_adjustments": "minimal"
    }
  },
  "solvency_metrics": {
    "debt_to_equity": 0.4,
    "interest_coverage": 15.0,
    "debt_service_coverage": 5.0,
    "covenant_compliance": {
      "status": "compliant",
      "key_ratios": ["Debt/EBITDA < 3.0"],
      "margin_of_safety": "20%"
    }
  },
  "earnings_quality": {
    "accruals_ratio": 0.05,
    "cash_earnings_correlation": 0.95,
    "revenue_quality_score": 4,
    "expense_management_score": 4,
    "accounting_red_flags": []
  },
  "risk_indicators": {
    "altman_z_score": {
      "value": 4.2,
      "interpretation": "Safe zone",
      "bankruptcy_probability": "1%"
    },
    "distress_signals": [],
    "early_warning_indicators": ["Transition to new licensing model"]
  },
  "peer_comparison": {
    "industry_position": "above_median",
    "key_differentiators": ["Strong revenue growth"],
    "competitive_advantages": ["Multi-year licensing"],
    "competitive_disadvantages": []
  },
  "recommendations": {
    "immediate_actions": [],
    "strategic_initiatives": ["Monitor licensing transition"],
    "monitoring_priorities": ["Revenue streams"],
    "stakeholder_communications": ["Highlight growth drivers"]
  },
  "confidence_metrics": {
    "data_quality": 5,
    "model_reliability": 4,
    "analyst_confidence": 5,
    "key_assumptions": ["Stable market conditions"]
  }
}

Example 2:
Paragraph: Our operating results are affected by foreign exchange rates. Approximately 27%, 25%, and 28% of our revenue was collected in foreign currencies during 2001, 2002, and 2003. Had the rates from fiscal 2002 been in effect in fiscal 2003, translated international revenue billed in local currencies would have been approximately $700 million lower. Certain manufacturing, selling distribution and support costs are disbursed in local currencies, and a portion of international revenue is hedged, thus offsetting a portion of the translation exposure.

Output:
{
  "financial_health_score": {
    "overall_score": 70,
    "percentile_rank": 60,
    "rating_equivalent": "BB",
    "trend_direction": "stable"
  },
  "liquidity_analysis": {
    "current_ratio": 1.8,
    "quick_ratio": 1.5,
    "cash_ratio": 1.0,
    "working_capital_trend": "stable",
    "liquidity_adequacy": "adequate",
    "cash_burn_analysis": {
      "monthly_burn_rate": "N/A",
      "runway_months": 18,
      "seasonal_adjustments": "currency fluctuations"
    }
  },
  "solvency_metrics": {
    "debt_to_equity": 0.6,
    "interest_coverage": 10.0,
    "debt_service_coverage": 3.5,
    "covenant_compliance": {
      "status": "compliant",
      "key_ratios": ["Foreign exposure < 30%"],
      "margin_of_safety": "15%"
    }
  },
  "earnings_quality": {
    "accruals_ratio": 0.1,
    "cash_earnings_correlation": 0.85,
    "revenue_quality_score": 3,
    "expense_management_score": 3,
    "accounting_red_flags": ["Currency translation exposure"]
  },
  "risk_indicators": {
    "altman_z_score": {
      "value": 3.5,
      "interpretation": "Grey zone",
      "bankruptcy_probability": "5%"
    },
    "distress_signals": ["Potential $700M revenue impact"],
    "early_warning_indicators": ["Increasing foreign revenue percentage"]
  },
  "peer_comparison": {
    "industry_position": "below_median",
    "key_differentiators": ["Hedging strategies"],
    "competitive_advantages": ["Partial hedging"],
    "competitive_disadvantages": ["High foreign currency exposure"]
  },
  "recommendations": {
    "immediate_actions": ["Enhance hedging coverage"],
    "strategic_initiatives": ["Diversify revenue sources"],
    "monitoring_priorities": ["Exchange rates"],
    "stakeholder_communications": ["Disclose hedging effectiveness"]
  },
  "confidence_metrics": {
    "data_quality": 4,
    "model_reliability": 4,
    "analyst_confidence": 4,
    "key_assumptions": ["Continued hedging"]
  }
}

**Output Format:**
{{
  "financial_health_score": {{
    "overall_score": 1-100,
    "percentile_rank": "integer",
    "rating_equivalent": "string",
    "trend_direction": "improving/stable/deteriorating"
  }},
  "liquidity_analysis": {{
    "current_ratio": "float",
    "quick_ratio": "float", 
    "cash_ratio": "float",
    "working_capital_trend": "string",
    "liquidity_adequacy": "sufficient/adequate/concerning/critical",
    "cash_burn_analysis": {{
      "monthly_burn_rate": "estimated value",
      "runway_months": "integer",
      "seasonal_adjustments": "string"
    }}
  }},
  "solvency_metrics": {{
    "debt_to_equity": "float",
    "interest_coverage": "float",
    "debt_service_coverage": "float",
    "covenant_compliance": {{
      "status": "compliant/at_risk/breach",
      "key_ratios": ["string"],
      "margin_of_safety": "percentage"
    }}
  }},
  "earnings_quality": {{
    "accruals_ratio": "float",
    "cash_earnings_correlation": "float",
    "revenue_quality_score": 1-5,
    "expense_management_score": 1-5,
    "accounting_red_flags": ["string"]
  }},
  "risk_indicators": {{
    "altman_z_score": {{
      "value": "float",
      "interpretation": "string",
      "bankruptcy_probability": "percentage"
    }},
    "distress_signals": ["string"],
    "early_warning_indicators": ["string"]
  }},
  "peer_comparison": {{
    "industry_position": "top_quartile/above_median/below_median/bottom_quartile",
    "key_differentiators": ["string"],
    "competitive_advantages": ["string"],
    "competitive_disadvantages": ["string"]
  }},
  "recommendations": {{
    "immediate_actions": ["string"],
    "strategic_initiatives": ["string"],
    "monitoring_priorities": ["string"],
    "stakeholder_communications": ["string"]
  }},
  "confidence_metrics": {{
    "data_quality": 1-5,
    "model_reliability": 1-5,
    "analyst_confidence": 1-5,
    "key_assumptions": ["string"]
  }}
}}

Paragraph: {paragraph}

Provide actionable insights with specific numerical thresholds and benchmarks where possible.""",
        version="3.0",
        expected_output_schema={
            "financial_health_score": "object",
            "liquidity_analysis": "object", 
            "solvency_metrics": "object",
            "earnings_quality": "object",
            "risk_indicators": "object",
            "peer_comparison": "object",
            "recommendations": "object",
            "confidence_metrics": "object"
        },
        display_type="financial_dashboard",
        self_eval_instruction="Base confidence on data completeness, model validation, and industry benchmark availability"
    ),

    # ==================== CYBERSECURITY RISK ASSESSMENT ====================
    "cybersecurity_risk_v2": PromptTemplate(
        template="""You are a cybersecurity risk specialist with expertise in NIST Cybersecurity Framework and financial services security.

Analyze the paragraph for cybersecurity risks using the Integrated Cyber Risk Assessment Model:

**Risk Categories:**
1. Data Security Risks:
   - Data breach & exfiltration
   - Personal data protection (GDPR, CCPA)
   - Intellectual property theft
   - Data integrity compromise

2. Infrastructure Risks:
   - System availability & business continuity
   - Network security vulnerabilities
   - Cloud security risks
   - Third-party vendor risks

3. Operational Risks:
   - Insider threats & privileged access
   - Social engineering & phishing
   - Ransomware & malware
   - Supply chain attacks

4. Compliance & Regulatory:
   - SEC cybersecurity disclosure (Item 106)
   - Financial sector regulations
   - International data transfer rules
   - Industry-specific requirements

**Threat Assessment:**
- Threat actor capabilities
- Attack vector likelihood
- Asset criticality
- Control effectiveness
- Incident response readiness

**Few-Shot Examples:**

Example 1:
Paragraph: The Company’s business and reputation are impacted by information technology system failures and network disruptions. The Company and its global supply chain are dependent on complex information technology systems and are exposed to information technology system failures or network disruptions caused by natural disasters, accidents, pipeline disruptions, acts of terrorism or war, computer viruses, physical or electronic break-ins, ransomware or other cybersecurity incidents, or other events or disruptions. System upgrades, redundancy and other continuity measures may be ineffective or inadequate, and the Company’s or its vendors’ business continuity and disaster recovery planning may not be sufficient for all eventualities. Such failures or disruptions can adversely impact the Company’s business by, among other things, preventing access to the Company’s online services, interfering with customer transactions or impeding the manufacturing and shipping of the Company’s products.

Output:
{
  "cyber_risk_profile": {
    "primary_threat_category": "Infrastructure Risks",
    "risk_severity": 8,
    "attack_likelihood": 4,
    "business_impact": 5,
    "composite_cyber_score": 16.0
  },
  "threat_landscape": {
    "threat_actors": ["cybercriminal", "nation_state"],
    "attack_vectors": ["ransomware", "computer viruses", "physical break-ins"],
    "target_assets": ["IT systems", "supply chain"],
    "vulnerability_assessment": {
      "critical_vulnerabilities": 2,
      "unpatched_systems": "20%",
      "security_debt": "medium"
    }
  },
  "control_effectiveness": {
    "preventive_controls": {
      "score": 3,
      "key_controls": ["System redundancy"],
      "gaps_identified": ["Inadequate disaster recovery"]
    },
    "detective_controls": {
      "score": 2,
      "monitoring_coverage": "70%",
      "detection_capabilities": ["Intrusion detection"]
    },
    "response_controls": {
      "score": 3,
      "incident_response_maturity": 3,
      "recovery_capabilities": ["Business continuity planning"]
    }
  },
  "regulatory_compliance": {
    "applicable_frameworks": ["NIST", "SEC Item 106"],
    "compliance_status": "partial",
    "disclosure_requirements": {
      "sec_item_106": "needs_update",
      "material_incidents": true,
      "board_oversight": "adequate"
    }
  },
  "financial_impact": {
    "potential_loss_estimate": {
      "low_scenario": "$10M",
      "medium_scenario": "$50M",
      "high_scenario": "$100M"
    },
    "business_disruption": {
      "downtime_risk": "days",
      "revenue_impact": "15%",
      "customer_impact": "high"
    },
    "recovery_costs": {
      "incident_response": "$5M",
      "system_restoration": "$20M",
      "legal_regulatory": "$10M"
    }
  },
  "mitigation_roadmap": {
    "immediate_actions": ["Enhance redundancy measures"],
    "short_term_initiatives": ["Improve disaster recovery planning"],
    "long_term_strategy": ["Adopt advanced cybersecurity frameworks"],
    "investment_priorities": ["Vendor risk management"]
  },
  "confidence_assessment": {
    "overall_confidence": 4,
    "threat_intelligence_quality": 4,
    "control_visibility": 3,
    "assessment_limitations": ["Limited vendor details"]
  }
}

Example 2:
Paragraph: Risks from hardware, software, and backup systems; personal/confidential data handling. Reliance on third parties and financial services industry for complex, high-speed transactions. Potential disruptions from system failures, cyberattacks, fraud, and supply chain issues.

Output:
{
  "cyber_risk_profile": {
    "primary_threat_category": "Data Security Risks",
    "risk_severity": 7,
    "attack_likelihood": 3,
    "business_impact": 4,
    "composite_cyber_score": 14.0
  },
  "threat_landscape": {
    "threat_actors": ["insider", "cybercriminal"],
    "attack_vectors": ["cyberattacks", "fraud"],
    "target_assets": ["personal data", "transactions"],
    "vulnerability_assessment": {
      "critical_vulnerabilities": 3,
      "unpatched_systems": "15%",
      "security_debt": "low"
    }
  },
  "control_effectiveness": {
    "preventive_controls": {
      "score": 4,
      "key_controls": ["Backup systems"],
      "gaps_identified": ["Third-party reliance"]
    },
    "detective_controls": {
      "score": 3,
      "monitoring_coverage": "80%",
      "detection_capabilities": ["Fraud detection"]
    },
    "response_controls": {
      "score": 4,
      "incident_response_maturity": 4,
      "recovery_capabilities": ["System recovery"]
    }
  },
  "regulatory_compliance": {
    "applicable_frameworks": ["PCI-DSS", "SEC Item 106"],
    "compliance_status": "compliant",
    "disclosure_requirements": {
      "sec_item_106": "compliant",
      "material_incidents": false,
      "board_oversight": "needs_improvement"
    }
  },
  "financial_impact": {
    "potential_loss_estimate": {
      "low_scenario": "$5M",
      "medium_scenario": "$20M",
      "high_scenario": "$50M"
    },
    "business_disruption": {
      "downtime_risk": "hours",
      "revenue_impact": "10%",
      "customer_impact": "medium"
    },
    "recovery_costs": {
      "incident_response": "$3M",
      "system_restoration": "$10M",
      "legal_regulatory": "$5M"
    }
  },
  "mitigation_roadmap": {
    "immediate_actions": ["Strengthen third-party controls"],
    "short_term_initiatives": ["Enhance data handling protocols"],
    "long_term_strategy": ["Invest in advanced fraud detection"],
    "investment_priorities": ["Cyber insurance"]
  },
  "confidence_assessment": {
    "overall_confidence": 4,
    "threat_intelligence_quality": 3,
    "control_visibility": 4,
    "assessment_limitations": ["General description of risks"]
  }
}

**Output Format:**
{{
  "cyber_risk_profile": {{
    "primary_threat_category": "string",
    "risk_severity": 1-10,
    "attack_likelihood": 1-5,
    "business_impact": 1-5,
    "composite_cyber_score": "calculated value"
  }},
  "threat_landscape": {{
    "threat_actors": ["nation_state", "cybercriminal", "insider", "hacktivist"],
    "attack_vectors": ["string"],
    "target_assets": ["string"],
    "vulnerability_assessment": {{
      "critical_vulnerabilities": "integer",
      "unpatched_systems": "percentage",
      "security_debt": "high/medium/low"
    }}
  }},
  "control_effectiveness": {{
    "preventive_controls": {{
      "score": 1-5,
      "key_controls": ["string"],
      "gaps_identified": ["string"]
    }},
    "detective_controls": {{
      "score": 1-5,
      "monitoring_coverage": "percentage",
      "detection_capabilities": ["string"]
    }},
    "response_controls": {{
      "score": 1-5,
      "incident_response_maturity": 1-5,
      "recovery_capabilities": ["string"]
    }}
  }},
  "regulatory_compliance": {{
    "applicable_frameworks": ["NIST", "ISO27001", "SOC2", "PCI-DSS"],
    "compliance_status": "compliant/partial/non_compliant",
    "disclosure_requirements": {{
      "sec_item_106": "compliant/needs_update/non_compliant",
      "material_incidents": "boolean",
      "board_oversight": "adequate/needs_improvement"
    }}
  }},
  "financial_impact": {{
    "potential_loss_estimate": {{
      "low_scenario": "dollar_amount",
      "medium_scenario": "dollar_amount", 
      "high_scenario": "dollar_amount"
    }},
    "business_disruption": {{
      "downtime_risk": "hours/days",
      "revenue_impact": "percentage",
      "customer_impact": "low/medium/high"
    }},
    "recovery_costs": {{
      "incident_response": "dollar_amount",
      "system_restoration": "dollar_amount",
      "legal_regulatory": "dollar_amount"
    }}
  }},
  "mitigation_roadmap": {{
    "immediate_actions": ["string"],
    "short_term_initiatives": ["string"],
    "long_term_strategy": ["string"],
    "investment_priorities": ["string"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 1-5,
    "threat_intelligence_quality": 1-5,
    "control_visibility": 1-5,
    "assessment_limitations": ["string"]
  }}
}}

Paragraph: {paragraph}

Focus on material cybersecurity risks with Energy transition expectations derive from hypothetical scenarios with substantial uncertainties, reflecting assumptions about future lower-emission systems.

Output:
{
  "esg_classification": {
    "primary_category": "Environmental",
    "specific_risk_area": "Climate Change",
    "materiality_score": 5,
    "stakeholder_impact": ["Investors", "Regulators", "Communities"]
  },
  "risk_assessment": {
    "financial_impact": {
      "magnitude": 4,
      "timeframe": "long-term",
      "impact_type": "cost/liability"
    },
    "reputation_risk": {
      "severity": 4,
      "media_sensitivity": "high",
      "stakeholder_concern": 5
    }
  },
  "regulatory_landscape": {
    "current_regulations": ["UN COP frameworks", "Canadian net zero objectives"],
    "emerging_requirements": ["GHG reduction targets"],
    "compliance_status": "at_risk"
  },
  "mitigation_strategies": {
    "current_initiatives": ["Emission reduction goals"],
    "effectiveness_rating": 3,
    "recommended_improvements": ["Invest in renewable energy transitions"],
    "industry_best_practices": ["Net zero commitments"]
  },
  "framework_alignment": {
    "sasb_metrics": ["GHG Emissions"],
    "gri_indicators": ["GRI 305: Emissions"],
    "tcfd_recommendations": ["Strategy and Metrics"],
    "un_sdg_alignment": ["SDG 13: Climate Action"]
  },
  "confidence_assessment": {
    "overall_confidence": 4,
    "data_availability": "medium",
    "framework_certainty": 5,
    "precedent_clarity": 4
  }
}

Example 2:
Paragraph: All phases (Upstream, Downstream, Chemical) subject to Canadian federal, provincial, territorial, municipal laws, and international conventions. Imposes restrictions, liabilities, and obligations on generation, handling, storage, transportation, treatment, and disposal of hazardous substances and waste. Regulates product qualities and compositions, aiming to reduce consumption or address environmental concerns, potentially impacting commodity prices, costs, and revenues.

Output:
{
  "esg_classification": {
    "primary_category": "Environmental",
    "specific_risk_area": "Pollution & Waste Management",
    "materiality_score": 4,
    "stakeholder_impact": ["Regulators", "Communities"]
  },
  "risk_assessment": {
    "financial_impact": {
      "magnitude": 3,
      "timeframe": "medium-term",
      "impact_type": "cost"
    },
    "reputation_risk": {
      "severity": 3,
      "media_sensitivity": "medium",
      "stakeholder_concern": 4
    }
  },
  "regulatory_landscape": {
    "current_regulations": ["Canadian environmental laws", "International conventions"],
    "emerging_requirements": ["Stricter waste management rules"],
    "compliance_status": "compliant"
  },
  "mitigation_strategies": {
    "current_initiatives": ["Compliance with laws"],
    "effectiveness_rating": 4,
    "recommended_improvements": ["Enhance waste reduction programs"],
    "industry_best_practices": ["Circular economy approaches"]
  },
  "framework_alignment": {
    "sasb_metrics": ["Waste & Hazardous Materials Management"],
    "gri_indicators": ["GRI 306: Waste"],
    "tcfd_recommendations": ["Risk Management"],
    "un_sdg_alignment": ["SDG 12: Responsible Consumption"]
  },
  "confidence_assessment": {
    "overall_confidence": 5,
    "data_availability": "high",
    "framework_certainty": 5,
    "precedent_clarity": 5
  }
}

**Output Format:**
{{
  "esg_classification": {{
    "primary_category": "Environmental/Social/Governance",
    "specific_risk_area": "string",
    "materiality_score": 1-5,
    "stakeholder_impact": ["investors", "customers", "employees", "communities", "regulators"]
  }},
  "risk_assessment": {{
    "financial_impact": {{
      "magnitude": 1-5,
      "timeframe": "short/medium/long-term",
      "impact_type": "revenue/cost/asset_value/liability"
    }},
    "reputation_risk": {{
      "severity": 1-5,
      "media_sensitivity": "high/medium/low",
      "stakeholder_concern": 1-5
    }}
  }},
  "regulatory_landscape": {{
    "current_regulations": ["string"],
    "emerging_requirements": ["string"],
    "compliance_status": "compliant/at_risk/non_compliant"
  }},
  "mitigation_strategies": {{
    "current_initiatives": ["string"],
    "effectiveness_rating": 1-5,
    "recommended_improvements": ["string"],
    "industry_best_practices": ["string"]
  }},
  "framework_alignment": {{
    "sasb_metrics": ["string"],
    "gri_indicators": ["string"], 
    "tcfd_recommendations": ["string"],
    "un_sdg_alignment": ["string"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 1-5,
    "data_availability": "high/medium/low",
    "framework_certainty": 1-5,
    "precedent_clarity": 1-5
  }}
}}

Paragraph: {paragraph}

Focus on material ESG risks with clear financial implications and stakeholder impact.""",
        version="2.0",
        expected_output_schema={
            "esg_classification": "object",
            "risk_assessment": "object",
            "regulatory_landscape": "object",
            "mitigation_strategies": "object",
            "framework_alignment": "object",
            "confidence_assessment": "object"
        },
        display_type="esg_dashboard",
        self_eval_instruction="Assess confidence based on ESG framework alignment, materiality evidence, and stakeholder impact clarity",
        regulation_mapping={
            "SEC": ["Climate Disclosure Rules", "Human Capital Disclosure"],
            "EU": ["SFDR", "EU Taxonomy", "CSRD"],
            "SASB": ["Industry Standards"],
            "TCFD": ["Climate Recommendations"]
        }
    ),

    # ==================== FINANCIAL HEALTH DIAGNOSTIC ====================
    "financial_health_v3": PromptTemplate(
        template="""You are a senior credit analyst with CFA and FRM credentials. Perform comprehensive financial health assessment using the Advanced Diagnostic Framework 3.0:

**Multi-Dimensional Analysis:**

1. Liquidity & Cash Flow Analysis:
   - Working capital adequacy assessment
   - Cash conversion cycle efficiency
   - Free cash flow sustainability
   - Liquidity coverage ratio (if applicable)
   - Debt maturity profile analysis

2. Solvency & Capital Structure:
   - Leverage ratios vs. industry benchmarks
   - Interest coverage capability
   - Debt covenant compliance status
   - Capital allocation efficiency
   - Off-balance sheet exposure

3. Profitability & Earnings Quality:
   - Revenue recognition practices
   - Margin sustainability analysis
   - Non-recurring items identification
   - Cash vs. accrual earnings correlation
   - Management guidance reliability

4. Risk-Adjusted Valuation:
   - Altman Z-Score calculation
   - Merton Distance-to-Default estimation
   - Peer group comparative analysis
   - Stress testing implications
   - Credit rating migration probability

**Diagnostic Indicators:**
- Red flags (immediate attention required)
- Yellow flags (monitoring recommended)
- Green flags (positive indicators)
- Trend analysis (improving/stable/deteriorating)

**Few-Shot Examples:**

Example 1:
Paragraph: Revenue growth in fiscal 2003 was driven primarily by multi-year licensing that occurred before the transition to our new licensing program (Licensing 6.0) in the first quarter of fiscal 2003. Prior to the July 31, 2002 transition date to Licensing 6.0, we experienced significant growth in multi-year licensing arrangements as customers enrolled in our maintenance programs, including Upgrade Advantage and Software Assurance. The revenue growth also reflected a $933 million or 13% increase associated with OEM licensing of Microsoft Windows operating systems and a $309 million or 23% increase in revenue from Microsoft Xbox video game consoles.

Output:
{
  "financial_health_score": {
    "overall_score": 85,
    "percentile_rank": 75,
    "rating_equivalent": "BBB+",
    "trend_direction": "improving"
  },
  "liquidity_analysis": {
    "current_ratio": 2.5,
    "quick_ratio": 2.0,
    "cash_ratio": 1.5,
    "working_capital_trend": "positive",
    "liquidity_adequacy": "sufficient",
    "cash_burn_analysis": {
      "monthly_burn_rate": "N/A",
      "runway_months": 24,
      "seasonal_adjustments": "minimal"
    }
  },
  "solvency_metrics": {
    "debt_to_equity": 0.5,
    "interest_coverage": 15.0,
    "debt_service_coverage": 5.0,
    "covenant_compliance": {
      "status": "compliant",
      "key_ratios": ["Debt/EBITDA < 3"],
      "margin_of_safety": "25%"
    }
  },
  "earnings_quality": {
    "accruals_ratio": 0.05,
    "cash_earnings_correlation": 0.95,
    "revenue_quality_score": 4,
    "expense_management_score": 4,
    "accounting_red_flags": []
  },
  "risk_indicators": {
    "altman_z_score": {
      "value": 4.2,
      "interpretation": "Safe zone",
      "bankruptcy_probability": "1%"
    },
    "distress_signals": [],
    "early_warning_indicators": ["Revenue growth from licensing"]
  },
  "peer_comparison": {
    "industry_position": "above_median",
    "key_differentiators": ["Strong OEM licensing"],
    "competitive_advantages": ["Multi-year arrangements"],
    "competitive_disadvantages": []
  },
  "recommendations": {
    "immediate_actions": [],
    "strategic_initiatives": ["Expand maintenance programs"],
    "monitoring_priorities": ["Licensing transitions"],
    "stakeholder_communications": ["Highlight revenue growth"
  },
  "confidence_metrics": {
    "data_quality": 5,
    "model_reliability": 4,
    "analyst_confidence": 5,
    "key_assumptions": ["Stable market conditions"]
  }
}

Example 2:
Paragraph: Our operating results are affected by foreign exchange rates. Approximately 27%, 25%, and 28% of our revenue was collected in foreign currencies during 2001, 2002, and 2003. Had the rates from fiscal 2002 been in effect in fiscal 2003, translated international revenue billed in local currencies would have been approximately $700 million lower. Certain manufacturing, selling distribution and support costs are disbursed in local currencies, and a portion of international revenue is hedged, thus offsetting a portion of the translation exposure.

Output:
{
  "financial_health_score": {
    "overall_score": 70,
    "percentile_rank": 60,
    "rating_equivalent": "BB+",
    "trend_direction": "stable"
  },
  "liquidity_analysis": {
    "current_ratio": 1.8,
    "quick_ratio": 1.5,
    "cash_ratio": 1.0,
    "working_capital_trend": "stable",
    "liquidity_adequacy": "adequate",
    "cash_burn_analysis": {
      "monthly_burn_rate": "N/A",
      "runway_months": 18,
      "seasonal_adjustments": "currency fluctuations"
    }
  },
  "solvency_metrics": {
    "debt_to_equity": 0.6,
    "interest_coverage": 10.0,
    "debt_service_coverage": 4.0,
    "covenant_compliance": {
      "status": "compliant",
      "key_ratios": ["Foreign exchange hedging"],
      "margin_of_safety": "20%"
    }
  },
  "earnings_quality": {
    "accruals_ratio": 0.1,
    "cash_earnings_correlation": 0.85,
    "revenue_quality_score": 3,
    "expense_management_score": 3,
    "accounting_red_flags": ["Currency translation exposure"]
  },
  "risk_indicators": {
    "altman_z_score": {
      "value": 3.5,
      "interpretation": "Grey zone",
      "bankruptcy_probability": "5%"
    },
    "distress_signals": ["Foreign exchange volatility"],
    "early_warning_indicators": ["Hedging portion of revenue"]
  },
  "peer_comparison": {
    "industry_position": "below_median",
    "key_differentiators": ["International revenue exposure"],
    "competitive_advantages": ["Hedging strategies"],
    "competitive_disadvantages": ["Currency fluctuations impact"]
  },
  "recommendations": {
    "immediate_actions": ["Strengthen hedging"],
    "strategic_initiatives": ["Diversify currency exposure"],
    "monitoring_priorities": ["Exchange rates"],
    "stakeholder_communications": ["Disclose hedging effectiveness"]
  },
  "confidence_metrics": {
    "data_quality": 4,
    "model_reliability": 4,
    "analyst_confidence": 4,
    "key_assumptions": ["Continued hedging"]
  }
}

**Output Format:**
{{
  "financial_health_score": {{
    "overall_score": 1-100,
    "percentile_rank": "integer",
    "rating_equivalent": "string",
    "trend_direction": "improving/stable/deteriorating"
  }},
  "liquidity_analysis": {{
    "current_ratio": "float",
    "quick_ratio": "float", 
    "cash_ratio": "float",
    "working_capital_trend": "string",
    "liquidity_adequacy": "sufficient/adequate/concerning/critical",
    "cash_burn_analysis": {{
      "monthly_burn_rate": "estimated value",
      "runway_months": "integer",
      "seasonal_adjustments": "string"
    }}
  }},
  "solvency_metrics": {{
    "debt_to_equity": "float",
    "interest_coverage": "float",
    "debt_service_coverage": "float",
    "covenant_compliance": {{
      "status": "compliant/at_risk/breach",
      "key_ratios": ["string"],
      "margin_of_safety": "percentage"
    }}
  }},
  "earnings_quality": {{
    "accruals_ratio": "float",
    "cash_earnings_correlation": "float",
    "revenue_quality_score": 1-5,
    "expense_management_score": 1-5,
    "accounting_red_flags": ["string"]
  }},
  "risk_indicators": {{
    "altman_z_score": {{
      "value": "float",
      "interpretation": "string",
      "bankruptcy_probability": "percentage"
    }},
    "distress_signals": ["string"],
    "early_warning_indicators": ["string"]
  }},
  "peer_comparison": {{
    "industry_position": "top_quartile/above_median/below_median/bottom_quartile",
    "key_differentiators": ["string"],
    "competitive_advantages": ["string"],
    "competitive_disadvantages": ["string"]
  }},
  "recommendations": {{
    "immediate_actions": ["string"],
    "strategic_initiatives": ["string"],
    "monitoring_priorities": ["string"],
    "stakeholder_communications": ["string"]
  }},
  "confidence_metrics": {{
    "data_quality": 1-5,
    "model_reliability": 1-5,
    "analyst_confidence": 1-5,
    "key_assumptions": ["string"]
  }}
}}

Paragraph: {paragraph}

Provide actionable insights with specific numerical thresholds and benchmarks where possible.""",
        version="3.0",
        expected_output_schema={
            "financial_health_score": "object",
            "liquidity_analysis": "object", 
            "solvency_metrics": "object",
            "earnings_quality": "object",
            "risk_indicators": "object",
            "peer_comparison": "object",
            "recommendations": "object",
            "confidence_metrics": "object"
        },
        display_type="financial_dashboard",
        self_eval_instruction="Base confidence on data completeness, model validation, and industry benchmark availability"
    ),

    # ==================== CYBERSECURITY RISK ASSESSMENT ====================
    "cybersecurity_risk_v2": PromptTemplate(
        template="""You are a cybersecurity risk specialist with expertise in NIST Cybersecurity Framework and financial services security.

Analyze the paragraph for cybersecurity risks using the Integrated Cyber Risk Assessment Model:

**Risk Categories:**
1. Data Security Risks:
   - Data breach & exfiltration
   - Personal data protection (GDPR, CCPA)
   - Intellectual property theft
   - Data integrity compromise

2. Infrastructure Risks:
   - System availability & business continuity
   - Network security vulnerabilities
   - Cloud security risks
   - Third-party vendor risks

3. Operational Risks:
   - Insider threats & privileged access
   - Social engineering & phishing
   - Ransomware & malware
   - Supply chain attacks

4. Compliance & Regulatory:
   - SEC cybersecurity disclosure (Item 106)
   - Financial sector regulations
   - International data transfer rules
   - Industry-specific requirements

**Threat Assessment:**
- Threat actor capabilities
- Attack vector likelihood
- Asset criticality
- Control effectiveness
- Incident response readiness

**Few-Shot Examples:**

Example 1:
Paragraph: The Company’s business and reputation are impacted by information technology system failures and network disruptions. The Company and its global supply chain are dependent on complex information technology systems and are exposed to information technology system failures or network disruptions caused by natural disasters, accidents, power disruptions, telecommunications failures, acts of terrorism or war, computer viruses, physical or electronic break-ins, ransomware or other cybersecurity incidents, or other events or disruptions. System upgrades, redundancy and other continuity measures may be ineffective or inadequate, and the Company’s or its vendors’ business continuity and disaster recovery planning may not be sufficient for all eventualities. Such failures or disruptions can adversely impact the Company’s business by, among other things, preventing access to the Company’s online services, interfering with customer transactions or impeding the manufacturing and shipping of the Company’s products.

Output:
{
  "cyber_risk_profile": {
    "primary_threat_category": "Infrastructure Risks",
    "risk_severity": 8,
    "attack_likelihood": 4,
    "business_impact": 5,
    "composite_cyber_score": 16.0
  },
  "threat_landscape": {
    "threat_actors": ["cybercriminal", "nation_state"],
    "attack_vectors": ["ransomware", "network disruptions"],
    "target_assets": ["IT systems", "supply chain"],
    "vulnerability_assessment": {
      "critical_vulnerabilities": 2,
      "unpatched_systems": "10%",
      "security_debt": "medium"
    }
  },
  "control_effectiveness": {
    "preventive_controls": {
      "score": 3,
      "key_controls": ["System upgrades", "Redundancy measures"],
      "gaps_identified": ["Inadequate for all eventualities"]
    },
    "detective_controls": {
      "score": 3,
      "monitoring_coverage": "80%",
      "detection_capabilities": ["Business continuity planning"]
    },
    "response_controls": {
      "score": 2,
      "incident_response_maturity": 3,
      "recovery_capabilities": ["Disaster recovery planning"]
    }
  },
  "regulatory_compliance": {
    "applicable_frameworks": ["NIST", "SEC Item 106"],
    "compliance_status": "partial",
    "disclosure_requirements": {
      "sec_item_106": "needs_update",
      "material_incidents": true,
      "board_oversight": "needs_improvement"
    }
  },
  "financial_impact": {
    "potential_loss_estimate": {
      "low_scenario": "$10M",
      "medium_scenario": "$50M",
      "high_scenario": "$200M"
    },
    "business_disruption": {
      "downtime_risk": "days",
      "revenue_impact": "15%",
      "customer_impact": "high"
    },
    "recovery_costs": {
      "incident_response": "$5M",
      "system_restoration": "$10M",
      "legal_regulatory": "$20M"
    }
  },
  "mitigation_roadmap": {
    "immediate_actions": ["Enhance redundancy measures"],
    "short_term_initiatives": ["Improve disaster recovery planning"],
    "long_term_strategy": ["Adopt advanced cybersecurity frameworks"],
    "investment_priorities": ["Vendor risk management"]
  },
  "confidence_assessment": {
    "overall_confidence": 4,
    "threat_intelligence_quality": 4,
    "control_visibility": 3,
    "assessment_limitations": ["Vendor dependencies"]
  }
}

Example 2:
Paragraph: Risks from hardware, software, and backup systems; personal/confidential data handling. Reliance on third parties and financial services industry for complex, high-speed transactions. Potential disruptions from system failures, cyberattacks, fraud, and supply chain issues.

Output:
{
  "cyber_risk_profile": {
    "primary_threat_category": "Data Security Risks",
    "risk_severity": 7,
    "attack_likelihood": 4,
    "business_impact": 4,
    "composite_cyber_score": 14.0
  },
  "threat_landscape": {
    "threat_actors": ["cybercriminal", "insider"],
    "attack_vectors": ["cyberattacks", "fraud"],
    "target_assets": ["Personal data", "Backup systems"],
    "vulnerability_assessment": {
      "critical_vulnerabilities": 3,
      "unpatched_systems": "15%",
      "security_debt": "high"
    }
  },
  "control_effectiveness": {
    "preventive_controls": {
      "score": 2,
      "key_controls": ["Third-party reliance"],
      "gaps_identified": ["System failures"]
    },
    "detective_controls": {
      "score": 3,
      "monitoring_coverage": "70%",
      "detection_capabilities": ["Fraud detection"]
    },
    "response_controls": {
      "score": 3,
      "incident_response_maturity": 4,
      "recovery_capabilities": ["Supply chain recovery"]
    }
  },
  "regulatory_compliance": {
    "applicable_frameworks": ["GDPR", "CCPA"],
    "compliance_status": "non_compliant",
    "disclosure_requirements": {
      "sec_item_106": "non_compliant",
      "material_incidents": true,
      "board_oversight": "adequate"
    }
  },
  "financial_impact": {
    "potential_loss_estimate": {
      "low_scenario": "$5M",
      "medium_scenario": "$30M",
      "high_scenario": "$100M"
    },
    "business_disruption": {
      "downtime_risk": "hours",
      "revenue_impact": "10%",
      "customer_impact": "medium"
    },
    "recovery_costs": {
      "incident_response": "$3M",
      "system_restoration": "$8M",
      "legal_regulatory": "$15M"
    }
  },
  "mitigation_roadmap": {
    "immediate_actions": ["Strengthen data handling controls"],
    "short_term_initiatives": ["Third-party audits"],
    "long_term_strategy": ["Advancedencryption"],
    "investment_priorities": ["Cybersecurity training"]
  },
  "confidence_assessment": {
    "overall_confidence": 3,
    "threat_intelligence_quality": 3,
    "control_visibility": 4,
    "assessment_limitations": ["Limited details on third parties"]
  }
}

**Output Format:**
{{
  "cyber_risk_profile": {{
    "primary_threat_category": "string",
    "risk_severity": 1-10,
    "attack_likelihood": 1-5,
    "business_impact": 1-5,
    "composite_cyber_score": "calculated value"
  }},
  "threat_landscape": {{
    "threat_actors": ["nation_state", "cybercriminal", "insider", "hacktivist"],
    "attack_vectors": ["string"],
    "target_assets": ["string"],
    "vulnerability_assessment": {{
      "critical_vulnerabilities": "integer",
      "unpatched_systems": "percentage",
      "security_debt": "high/medium/low"
    }}
  }},
  "control_effectiveness": {{
    "preventive_controls": {{
      "score": 1-5,
      "key_controls": ["string"],
      "gaps_identified": ["string"]
    }},
    "detective_controls": {{
      "score": 1-5,
      "monitoring_coverage": "percentage",
      "detection_capabilities": ["string"]
    }},
    "response_controls": {{
      "score": 1-5,
      "incident_response_maturity": 1-5,
      "recovery_capabilities": ["string"]
    }}
  }},
  "regulatory_compliance": {{
    "applicable_frameworks": ["NIST", "ISO27001", "SOC2", "PCI-DSS"],
    "compliance_status": "compliant/partial/non_compliant",
    "disclosure_requirements": {{
      "sec_item_106": "compliant/needs_update/non_compliant",
      "material_incidents": "boolean",
      "board_oversight": "adequate/needs_improvement"
    }}
  }},
  "financial_impact": {{
    "potential_loss_estimate": {{
      "low_scenario": "dollar_amount",
      "medium_scenario": "dollar_amount", 
      "high_scenario": "dollar_amount"
    }},
    "business_disruption": {{
      "downtime_risk": "hours/days",
      "revenue_impact": "percentage",
      "customer_impact": "low/medium/high"
    }},
    "recovery_costs": {{
      "incident_response": "dollar_amount",
      "system_restoration": "dollar_amount",
      "legal_regulatory": "dollar_amount"
    }}
  }},
  "mitigation_roadmap": {{
    "immediate_actions": ["string"],
    "short_term_initiatives": ["string"],
    "long_term_strategy": ["string"],
    "investment_priorities": ["string"]
  }},
  "confidence_assessment": {{
    "overall_confidence": 1-5,
    "threat_intelligence_quality": 1-5,
    "control_visibility": 1-5,
    "assessment_limitations": ["string"]
  }}
}}

Paragraph: {paragraph}

Focus on material cybersecurity risks with quantifiable business impact and regulatory implications.""",
        version="2.0",
        expected_output_schema={
            "cyber_risk_profile": "object",
            "threat_landscape": "object",
            "control_effectiveness": "object", 
            "regulatory_compliance": "object",
            "financial_impact": "object",
            "mitigation_roadmap": "object",
            "confidence_assessment": "object"
        },
        display_type="cybersecurity_dashboard",
        self_eval_instruction="Evaluate confidence based on threat intelligence, control visibility, and incident precedent",
        regulation_mapping={
            "SEC": ["Item 106 - Cybersecurity"],
            "NIST": ["Cybersecurity Framework"],
            "GDPR": ["Data Protection"],
            "CCPA": ["Consumer Privacy"]
        }
    ),

    # ==================== OPERATIONAL RESILIENCE ====================
    "operational_resilience_v2": PromptTemplate(
        template="""You are an operational risk expert specializing in business continuity and operational resilience.

Assess operational resilience using the Integrated Operational Risk Framework:

**Resilience Dimensions:**
1. Process Resilience:
   - Critical process identification
   - Single points of failure
   - Process automation & redundancy
   - Error rates & quality metrics

2. Technology Resilience:
   - System availability & uptime
   - Disaster recovery capabilities
   - Technology debt assessment
   - Digital transformation risks

3. People Resilience:
   - Key person dependencies
   - Skills gap analysis
   - Succession planning
   - Cultural risk factors

4. Third-Party Resilience:
   - Vendor concentration risk
   - Supply chain vulnerabilities
   - Outsourcing risks
   - Partner relationship management

**Impact Assessment:**
- Service delivery impact
- Customer experience degradation
- Financial losses
- Regulatory consequences
- Reputational damage

**Few-Shot Examples:**

Example 1:
Paragraph: Risks from hardware, software, and backup systems; personal/confidential data handling. Reliance on third parties and financial services industry for complex, high-speed transactions. Potential disruptions from system failures, cyberattacks, fraud, and supply chain issues.

Output:
{
  "resilience_assessment": {
    "overall_resilience_score": 6,
    "critical_vulnerabilities": 3,
    "recovery_capability": "adequate",
    "stress_test_results": "conditional"
  },
  "process_analysis": {
    "critical_processes": ["Transaction processing"],
    "failure_points": ["System failures"],
    "automation_level": "80%",
    "quality_metrics": {
      "error_rate": "5%",
      "sla_compliance": "95%",
      "customer_satisfaction": 4
    }
  },
  "technology_infrastructure": {
    "system_availability": "99%",
    "recovery_time_objective": "4 hours",
    "recovery_point_objective": "1 hour",
    "technology_debt": {
      "legacy_systems": "30%",
      "security_patches": "behind",
      "modernization_priority": "high"
    }
  },
  "human_capital": {
    "key_person_risk": "medium",
    "succession_coverage": "70%",
    "skills_gap_severity": 3,
    "training_effectiveness": 4
  },
  "third_party_dependencies": {
    "vendor_concentration": "high",
    "critical_suppliers": 5,
    "backup_options": "limited",
    "monitoring_effectiveness": 3
  },
  "scenario_analysis": {
    "stress_scenarios": ["Cyberattack", "Supply chain disruption"],
    "impact_assessment": {
      "mild_stress": "low operational impact",
      "moderate_stress": "medium operational impact",
      "severe_stress": "high operational impact"
    },
    "recovery_strategies": ["Backup systems activation"]
  },
  "improvement_recommendations": {
    "priority_actions": ["Enhance third-party monitoring"],
    "investment_requirements": "$10M",
    "timeline_for_implementation": "6 months",
    "success_metrics": ["Reduced downtime"]
  },
  "confidence_metrics": {
    "assessment_confidence": 4,
    "data_completeness": "80%",
    "model_validation": 4,
    "expert_consensus": 5
  }
}

Example 2:
Paragraph: Operational risk defined as loss from inadequate processes, systems, people, or external events. Risk Framework approved by Board’s Enterprise Risk Committee (ERC) and Board, setting roles, responsibilities, and risk appetite limits.

Output:
{
  "resilience_assessment": {
    "overall_resilience_score": 7,
    "critical_vulnerabilities": 2,
    "recovery_capability": "strong",
    "stress_test_results": "passed"
  },
  "process_analysis": {
    "critical_processes": ["Risk management processes"],
    "failure_points": ["Inadequate processes"],
    "automation_level": "70%",
    "quality_metrics": {
      "error_rate": "3%",
      "sla_compliance": "98%",
      "customer_satisfaction": 4
    }
  },
  "technology_infrastructure": {
    "system_availability": "99.5%",
    "recovery_time_objective": "2 hours",
    "recovery_point_objective": "30 minutes",
    "technology_debt": {
      "legacy_systems": "15%",
      "security_patches": "current",
      "modernization_priority": "medium"
    }
  },
  "human_capital": {
    "key_person_risk": "low",
    "succession_coverage": "90%",
    "skills_gap_severity": 2,
    "training_effectiveness": 5
  },
  "third_party_dependencies": {
    "vendor_concentration": "medium",
    "critical_suppliers": 3,
    "backup_options": "adequate",
    "monitoring_effectiveness": 4
  },
  "scenario_analysis": {
    "stress_scenarios": ["External events"],
    "impact_assessment": {
      "mild_stress": "minimal impact",
      "moderate_stress": "low impact",
      "severe_stress": "medium impact"
    },
    "recovery_strategies": ["Risk appetite limits"]
  },
  "improvement_recommendations": {
    "priority_actions": ["Strengthen risk framework"],
    "investment_requirements": "$5M",
    "timeline_for_implementation": "12 months",
    "success_metrics": ["Improved resilience score"]
  },
  "confidence_metrics": {
    "assessment_confidence": 5,
    "data_completeness": "90%",
    "model_validation": 5,
    "expert_consensus": 5
  }
}

**Output Format:**
{{
  "resilience_assessment": {{
    "overall_resilience_score": 1-10,
    "critical_vulnerabilities": "integer",
    "recovery_capability": "strong/adequate/weak",
    "stress_test_results": "passed/conditional/failed"
  }},
  "process_analysis": {{
    "critical_processes": ["string"],
    "failure_points": ["string"],
    "automation_level": "percentage",
    "quality_metrics": {{
      "error_rate": "percentage",
      "sla_compliance": "percentage",
      "customer_satisfaction": 1-5
    }}
  }},
  "technology_infrastructure": {{
    "system_availability": "percentage",
    "recovery_time_objective": "hours",
    "recovery_point_objective": "hours", 
    "technology_debt": {{
      "legacy_systems": "percentage",
      "security_patches": "current/behind",
      "modernization_priority": "high/medium/low"
    }}
  }},
  "human_capital": {{
    "key_person_risk": "high/medium/low",
    "succession_coverage": "percentage",
    "skills_gap_severity": 1-5,
    "training_effectiveness": 1-5
  }},
  "third_party_dependencies": {{
    "vendor_concentration": "high/medium/low",
    "critical_suppliers": "integer",
    "backup_options": "adequate/limited/none",
    "monitoring_effectiveness": 1-5
  }},
  "scenario_analysis": {{
    "stress_scenarios": ["string"],
    "impact_assessment": {{
      "mild_stress": "operational_impact",
      "moderate_stress": "operational_impact",
      "severe_stress": "operational_impact"
    }},
    "recovery_strategies": ["string"]
  }},
  "improvement_recommendations": {{
    "priority_actions": ["string"],
    "investment_requirements": "dollar_estimate",
    "timeline_for_implementation": "months",
    "success_metrics": ["string"]
  }},
  "confidence_metrics": {{
    "assessment_confidence": 1-5,
    "data_completeness": "percentage",
    "model_validation": 1-5,
    "expert_consensus": 1-5
  }}
}}

Paragraph: {paragraph}

Provide specific, actionable recommendations for improving operational resilience.""",
        version="2.0",
        expected_output_schema={
            "resilience_assessment": "object",
            "process_analysis": "object",
            "technology_infrastructure": "object",
            "human_capital": "object", 
            "third_party_dependencies": "object",
            "scenario_analysis": "object",
            "improvement_recommendations": "object",
            "confidence_metrics": "object"
        },
        display_type="resilience_dashboard",
        self_eval_instruction="Base confidence on operational data quality, scenario testing results, and industry benchmarks"
    )
}

# Compliance regulation mapping for quick reference
REGULATION_CODES = {
    "SOX": {
        "302": "CEO/CFO Certifications",
        "404": "Management Assessment of Internal Controls", 
        "906": "Criminal Penalties for False Certifications"
    },
    "SEC": {
        "Item_105": "Risk Factors",
        "Item_303": "Management's Discussion and Analysis",
        "Item_402": "Executive Compensation",
        "Item_106": "Cybersecurity",
        "Reg_G": "Non-GAAP Financial Measures",
        "Reg_FD": "Fair Disclosure"
    },
    "FINRA": {
        "2020": "Use of Manipulative, Deceptive Devices",
        "2210": "Communications with the Public", 
        "5210": "Publication of Transactions and Quotations"
    },
    "Basel": {
        "Pillar_1": "Minimum Capital Requirements",
        "Pillar_2": "Supervisory Review Process",
        "Pillar_3": "Market Discipline"
    }
}

# Confidence threshold definitions
CONFIDENCE_THRESHOLDS = {
    "very_high": 4.5,
    "high": 3.5,
    "medium": 2.5, 
    "low": 1.5,
    "very_low": 1.0
}

# Risk severity mappings
SEVERITY_MAPPINGS = {
    "critical": {"min": 8, "max": 10, "description": "Immediate action required"},
    "high": {"min": 6, "max": 7, "description": "Significant concern"},
    "medium": {"min": 4, "max": 5, "description": "Moderate risk"},
    "low": {"min": 2, "max": 3, "description": "Minor issue"},
    "minimal": {"min": 1, "max": 1, "description": "Informational"}
}

def get_prompt_by_id(prompt_id: str) -> PromptTemplate:
    """Get prompt template by ID"""
    if prompt_id not in PROMPT_REGISTRY:
        raise ValueError(f"Prompt ID '{prompt_id}' not found in registry")
    return PROMPT_REGISTRY[prompt_id]

def get_applicable_regulations(risk_type: str) -> List[str]:
    """Get applicable regulations for a risk type"""
    regulation_map = {
        "Regulatory Risk": ["SOX", "SEC", "FINRA"],
        "Financial Risk": ["SOX", "SEC", "Basel"],
        "Cybersecurity Risk": ["SEC", "NIST", "GDPR"],
        "ESG Risk": ["SEC", "EU", "SASB"],
        "Operational Risk": ["SOX", "Basel"],
        "Market Risk": ["Basel", "SEC"],
        "Credit Risk": ["Basel", "SEC"]
    }
    return regulation_map.get(risk_type, ["SEC"])

def calculate_composite_risk_score(severity: int, velocity: int, confidence: float) -> float:
    """Calculate composite risk score"""
    base_score = (severity * velocity) / 2
    confidence_adjustment = confidence / 5.0
    return round(base_score * confidence_adjustment, 2)
