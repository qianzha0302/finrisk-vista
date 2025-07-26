import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const openAIApiKey = Deno.env.get('OPENAI_API_KEY');

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const PROMPT_TEMPLATES = {
  'risk_classifier': {
    name: 'Risk Classification',
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

**Output Format:**
{
  "risk_classification": {
    "primary_risk_type": "string",
    "secondary_risk_types": ["string"],
    "severity_score": 1-10,
    "velocity_score": 1-5,
    "composite_risk_score": "calculated value"
  },
  "risk_details": {
    "risk_driver": "string",
    "potential_impact": "string", 
    "affected_stakeholders": ["string"],
    "key_excerpt": "most relevant 50-100 words"
  },
  "mitigation_analysis": {
    "existing_controls": ["string"],
    "control_effectiveness": 1-5,
    "recommended_actions": ["string"],
    "urgency_level": "immediate/high/medium/low"
  },
  "confidence_assessment": {
    "overall_confidence": 1-5,
    "reasoning": ["basis for confidence rating"],
    "data_quality": "high/medium/low"
  }
}

Paragraph: {paragraph}

Respond ONLY with the JSON object.`
  },
  'compliance_audit_v2': {
    name: 'Compliance Audit',
    template: `You are a compliance expert with expertise in SEC, FINRA, SOX, and Basel regulations.

Conduct comprehensive compliance review of the 10-K section:

**Regulatory Framework Check:**
1. SEC Disclosure Requirements:
   - Item 105 (Risk Factors) - completeness and materiality
   - Item 303 (MD&A) - forward-looking statements compliance
   - Item 402 (Executive Compensation) - proxy disclosure rules

2. SOX Compliance:
   - Section 302 - CEO/CFO certifications
   - Section 404 - internal controls assessment
   - Section 906 - criminal penalties for false certifications

**Output Format:**
{
  "compliance_assessment": {
    "overall_status": "compliant/non-compliant/requires_review",
    "compliance_score": 1-10,
    "critical_issues_count": "integer"
  },
  "regulatory_findings": [
    {
      "regulation": "string",
      "section": "string", 
      "finding_type": "violation/deficiency/best_practice",
      "severity": 1-5,
      "description": "string",
      "supporting_text": "relevant excerpt"
    }
  ],
  "disclosure_gaps": [
    {
      "required_disclosure": "string",
      "current_status": "missing/inadequate/unclear",
      "regulatory_basis": "specific rule/section",
      "recommended_action": "string"
    }
  ]
}

Paragraph: {paragraph}

Focus on identifying specific regulatory violations and providing actionable remediation steps.`
  },
  'esg_risk_v2': {
    name: 'ESG Risk Assessment',
    template: `You are an ESG risk specialist with expertise in SASB, GRI, and TCFD frameworks.

Analyze the paragraph for ESG-related risks:

**Assessment Framework:**
1. Environmental Risks:
   - Climate change (physical & transition risks)
   - Resource scarcity (water, energy, raw materials)
   - Pollution & waste management

2. Social Risks:
   - Labor practices & human rights
   - Supply chain responsibility  
   - Product safety & quality
   - Community relations

3. Governance Risks:
   - Board composition & independence
   - Executive compensation alignment
   - Business ethics & corruption
   - Transparency & disclosure

**Output Format:**
{
  "esg_classification": {
    "primary_category": "Environmental/Social/Governance",
    "specific_risk_area": "string",
    "materiality_score": 1-5,
    "stakeholder_impact": ["investors", "customers", "employees", "communities", "regulators"]
  },
  "risk_assessment": {
    "financial_impact": {
      "magnitude": 1-5,
      "timeframe": "short/medium/long-term",
      "impact_type": "revenue/cost/asset_value/liability"
    },
    "reputation_risk": {
      "severity": 1-5,
      "media_sensitivity": "high/medium/low",
      "stakeholder_concern": 1-5
    }
  },
  "mitigation_strategies": {
    "current_initiatives": ["string"],
    "effectiveness_rating": 1-5,
    "recommended_improvements": ["string"]
  }
}

Paragraph: {paragraph}

Focus on material ESG risks with clear financial implications.`
  },
  'financial_health_v3': {
    name: 'Financial Health Diagnostic',
    template: `You are a senior credit analyst with CFA and FRM credentials. Perform comprehensive financial health assessment:

**Multi-Dimensional Analysis:**
1. Liquidity & Cash Flow Analysis:
   - Working capital adequacy assessment
   - Cash conversion cycle efficiency
   - Free cash flow sustainability

2. Solvency & Capital Structure:
   - Leverage ratios vs. industry benchmarks
   - Interest coverage capability
   - Debt covenant compliance status

3. Profitability & Earnings Quality:
   - Revenue recognition practices
   - Margin sustainability analysis
   - Non-recurring items identification

**Output Format:**
{
  "financial_health_score": {
    "overall_score": 1-100,
    "rating_equivalent": "string",
    "trend_direction": "improving/stable/deteriorating"
  },
  "liquidity_analysis": {
    "liquidity_adequacy": "sufficient/adequate/concerning/critical",
    "working_capital_trend": "string",
    "cash_burn_analysis": {
      "runway_months": "integer",
      "seasonal_adjustments": "string"
    }
  },
  "solvency_metrics": {
    "covenant_compliance": {
      "status": "compliant/at_risk/breach",
      "key_ratios": ["string"],
      "margin_of_safety": "percentage"
    }
  },
  "recommendations": {
    "immediate_actions": ["string"],
    "strategic_initiatives": ["string"],
    "monitoring_priorities": ["string"]
  }
}

Paragraph: {paragraph}

Provide actionable insights with specific numerical thresholds.`
  },
  'cybersecurity_risk_v2': {
    name: 'Cybersecurity Risk',
    template: `You are a cybersecurity risk specialist with expertise in NIST Cybersecurity Framework.

Analyze the paragraph for cybersecurity risks:

**Risk Categories:**
1. Data Security Risks:
   - Data breach & exfiltration
   - Personal data protection (GDPR, CCPA)
   - Intellectual property theft

2. Infrastructure Risks:
   - System availability & business continuity
   - Network security vulnerabilities
   - Cloud security risks
   - Third-party vendor risks

3. Operational Risks:
   - Insider threats & privileged access
   - Social engineering & phishing
   - Ransomware & malware

**Output Format:**
{
  "cyber_risk_profile": {
    "primary_threat_category": "string",
    "risk_severity": 1-10,
    "attack_likelihood": 1-5,
    "business_impact": 1-5
  },
  "threat_landscape": {
    "threat_actors": ["nation_state", "cybercriminal", "insider", "hacktivist"],
    "attack_vectors": ["string"],
    "target_assets": ["string"]
  },
  "control_effectiveness": {
    "preventive_controls": {
      "score": 1-5,
      "key_controls": ["string"],
      "gaps_identified": ["string"]
    }
  },
  "financial_impact": {
    "potential_loss_estimate": {
      "low_scenario": "dollar_amount",
      "high_scenario": "dollar_amount"
    },
    "business_disruption": {
      "downtime_risk": "hours/days",
      "revenue_impact": "percentage"
    }
  },
  "mitigation_roadmap": {
    "immediate_actions": ["string"],
    "investment_priorities": ["string"]
  }
}

Paragraph: {paragraph}

Focus on material cybersecurity risks with quantifiable business impact.`
  },
  'operational_resilience_v2': {
    name: 'Operational Resilience',
    template: `You are an operational risk expert specializing in business continuity and operational resilience.

Assess operational resilience:

**Resilience Dimensions:**
1. Process Resilience:
   - Critical process identification
   - Single points of failure
   - Process automation & redundancy

2. Technology Resilience:
   - System availability & uptime
   - Disaster recovery capabilities
   - Technology debt assessment

3. People Resilience:
   - Key person dependencies
   - Skills gap analysis
   - Succession planning

4. Third-Party Resilience:
   - Vendor concentration risk
   - Supply chain vulnerabilities
   - Outsourcing risks

**Output Format:**
{
  "resilience_assessment": {
    "overall_resilience_score": 1-10,
    "critical_vulnerabilities": "integer",
    "recovery_capability": "strong/adequate/weak"
  },
  "process_analysis": {
    "critical_processes": ["string"],
    "failure_points": ["string"],
    "automation_level": "percentage"
  },
  "technology_infrastructure": {
    "system_availability": "percentage",
    "recovery_time_objective": "hours",
    "technology_debt": {
      "legacy_systems": "percentage",
      "modernization_priority": "high/medium/low"
    }
  },
  "improvement_recommendations": {
    "priority_actions": ["string"],
    "investment_requirements": "dollar_estimate",
    "timeline_for_implementation": "months"
  }
}

Paragraph: {paragraph}

Provide specific, actionable recommendations for improving operational resilience.`
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