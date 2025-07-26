import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const openAIApiKey = Deno.env.get('OPENAI_API_KEY');

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const PROMPT_TEMPLATES = {
  'risk_classifier': {
    name: 'Enhanced Risk Classification',
    template: `You are a senior financial risk analyst with CFA and FRM certifications. 

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

**Few-Shot Examples:**

Example 1:
Paragraph: The Company's operations and performance depend significantly on global and regional economic conditions and adverse economic conditions can materially adversely affect the Company's business, results of operations and financial condition.

Output:
{
  "risk_classification": {
    "primary_risk_type": "Market Risk",
    "secondary_risk_types": ["Geopolitical Risk"],
    "severity_score": 7,
    "velocity_score": 3,
    "composite_risk_score": 10.5
  },
  "risk_details": {
    "risk_driver": "Adverse macroeconomic conditions",
    "potential_impact": "Reduced demand for products and services",
    "affected_stakeholders": ["Consumers", "Investors", "Suppliers"],
    "key_excerpt": "Adverse macroeconomic conditions can materially adversely affect the Company's business"
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

Paragraph: {paragraph}

Respond ONLY with the JSON object. Ensure all numeric fields are properly typed.`
  },
  'compliance_audit_v2': {
    name: 'Enhanced Compliance Audit',
    template: `You are a compliance expert with expertise in SEC, FINRA, SOX, and Basel regulations.

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

**Few-Shot Examples:**

Example 1:
Paragraph: While the Company relies on its partners to adhere to its supplier code of conduct, material violations of the supplier code of conduct could occur.

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

Paragraph: {paragraph}

Focus on identifying specific regulatory violations and providing actionable remediation steps.`
  },
  'esg_risk_v2': {
    name: 'ESG Risk Assessment',
    template: `You are an ESG risk specialist with expertise in SASB, GRI, and TCFD frameworks.

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

**Few-Shot Examples:**

Example 1:
Paragraph: Driven by climate change concerns, regulatory frameworks adopted to reduce GHG emissions from oil and gas production and use.

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

Paragraph: {paragraph}

Focus on material ESG risks with clear financial implications and stakeholder impact.`
  },
  'financial_health_v3': {
    name: 'Financial Health Diagnostic',
    template: `You are a senior credit analyst with CFA and FRM credentials. Perform comprehensive financial health assessment using the Advanced Diagnostic Framework 3.0:

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

**Few-Shot Examples:**

Example 1:
Paragraph: Revenue growth in fiscal 2003 was driven primarily by multi-year licensing that occurred before the transition to our new licensing program.

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

Paragraph: {paragraph}

Provide actionable insights with specific numerical thresholds and benchmarks where possible.`
  },
  'cybersecurity_risk_v2': {
    name: 'Cybersecurity Risk Assessment',
    template: `You are a cybersecurity risk specialist with expertise in NIST Cybersecurity Framework and financial services security.

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

**Few-Shot Examples:**

Example 1:
Paragraph: The Company's business and reputation are impacted by information technology system failures and network disruptions.

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

Paragraph: {paragraph}

Focus on material cybersecurity risks with quantifiable business impact.`
  },
  'operational_resilience_v2': {
    name: 'Operational Resilience Analysis',
    template: `You are an operational risk specialist focusing on business continuity and operational resilience.

Analyze the following paragraph for operational risks and resilience factors using the Operational Resilience Framework:

**Assessment Areas:**
1. Business Continuity Threats:
   - Supply chain disruptions
   - Critical process failures
   - Key person dependencies
   - Technology infrastructure risks

2. Resilience Capabilities:
   - Backup systems and redundancy
   - Crisis management procedures
   - Recovery time objectives
   - Stress testing results

3. Stakeholder Impact:
   - Customer service disruption
   - Regulatory compliance risks
   - Financial implications
   - Reputational damage

**Output Format:**
{
  "operational_assessment": {
    "resilience_score": 1-10,
    "vulnerability_level": "low/medium/high/critical",
    "business_impact": 1-5,
    "recovery_capability": 1-5
  },
  "risk_factors": {
    "supply_chain_risks": ["string"],
    "technology_dependencies": ["string"],
    "process_vulnerabilities": ["string"],
    "human_capital_risks": ["string"]
  },
  "mitigation_controls": {
    "existing_controls": ["string"],
    "control_effectiveness": 1-5,
    "gaps_identified": ["string"],
    "recommended_improvements": ["string"]
  },
  "business_impact": {
    "customer_impact": "low/medium/high",
    "financial_exposure": "estimated amount",
    "regulatory_implications": ["string"],
    "reputational_risk": 1-5
  },
  "recovery_planning": {
    "rto_assessment": "hours/days",
    "backup_capabilities": ["string"],
    "testing_frequency": "regular/periodic/insufficient",
    "improvement_priorities": ["string"]
  },
  "confidence_assessment": {
    "overall_confidence": 1-5,
    "data_completeness": "high/medium/low",
    "assessment_limitations": ["string"]
  }
}

Paragraph: {paragraph}

Focus on business continuity threats and resilience capabilities.`
  }
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { document, prompts } = await req.json();
    
    if (!document || !prompts || prompts.length === 0) {
      return new Response(JSON.stringify({ error: 'Document and prompts are required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log(`Starting risk analysis for document: ${document.name}`);
    console.log(`Selected prompts: ${prompts.join(', ')}`);

    const results = [];

    // Split document content into paragraphs (simple approach)
    const paragraphs = document.content
      .split('\n\n')
      .filter(p => p.trim().length > 100) // Only analyze substantial paragraphs
      .slice(0, 3); // Limit to first 3 paragraphs to reduce API calls

    console.log(`Processing ${paragraphs.length} paragraphs with ${prompts.length} prompts`);

    // Helper function to delay between API calls
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    for (const promptKey of prompts) {
      const promptTemplate = PROMPT_TEMPLATES[promptKey as keyof typeof PROMPT_TEMPLATES];
      
      if (!promptTemplate) {
        console.warn(`Prompt template not found: ${promptKey}`);
        continue;
      }

      // Process only the first paragraph for now to avoid rate limits
      const paragraph = paragraphs[0];
      if (!paragraph) continue;

      try {
        console.log(`Analyzing with prompt: ${promptKey}`);
        const prompt = promptTemplate.template.replace('{paragraph}', paragraph);
        
        // Add delay between requests to avoid rate limiting
        await delay(1000);
        
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${openAIApiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            messages: [
              { 
                role: 'system', 
                content: 'You are a financial risk analysis expert. Always respond with valid JSON in the exact format requested.' 
              },
              { role: 'user', content: prompt }
            ],
            temperature: 0.1,
            max_tokens: 1000,
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`OpenAI API error: ${response.status} ${response.statusText} - ${errorText}`);
          
          // If rate limited, create a fallback result
          if (response.status === 429) {
            console.log('Rate limited, creating fallback result');
            results.push({
              paragraph: paragraph.substring(0, 200) + '...',
              analysis: {
                risk_type: promptTemplate.name,
                severity: "Unknown - Rate Limited",
                summary: "Analysis was rate limited by OpenAI API. Please try again in a few minutes.",
                key_findings: ["API rate limit reached"],
                recommendations: ["Wait a few minutes before retrying", "Consider upgrading OpenAI API plan for higher limits"]
              },
              prompt: promptKey
            });
          }
          continue;
        }

        const data = await response.json();
        const rawOutput = data.choices[0].message.content;
        
        // Parse the JSON response
        let analysis;
        try {
          // Clean the output and parse JSON
          const cleanedOutput = rawOutput.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
          analysis = JSON.parse(cleanedOutput);
        } catch (parseError) {
          console.error(`Failed to parse JSON response: ${parseError}`);
          // Fallback analysis structure
          analysis = {
            risk_type: promptTemplate.name,
            severity: "Medium",
            summary: "Analysis parsing failed - manual review required",
            key_findings: ["Parse error occurred"],
            recommendations: ["Manual review recommended"]
          };
        }

        results.push({
          paragraph: paragraph.substring(0, 200) + '...', // Truncate for display
          analysis,
          prompt: promptKey
        });

      } catch (error) {
        console.error(`Error analyzing paragraph with prompt ${promptKey}:`, error);
      }
    }

    console.log(`Analysis completed. Generated ${results.length} results.`);

    return new Response(JSON.stringify({ results }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in risk-analysis function:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});