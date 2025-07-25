# utils/prompt_registry.py
# Enhanced Prompt Registry with Compliance Features and Self-Evaluation

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