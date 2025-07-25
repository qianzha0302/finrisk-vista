import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const openAIApiKey = Deno.env.get('OPENAI_API_KEY');

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface RiskAnalysisRequest {
  document: {
    id: string;
    name: string;
    content: string;
  };
  prompts: string[];
}

const PROMPT_TEMPLATES = {
  'credit_risk': {
    name: 'Credit Risk Analysis',
    template: `Analyze the following text for credit risk indicators. Return a JSON response with this exact structure:
{
  "risk_type": "Credit Risk",
  "severity": "High/Medium/Low",
  "summary": "Brief summary of credit risk findings",
  "key_findings": ["finding1", "finding2", "finding3"],
  "recommendations": ["recommendation1", "recommendation2"]
}

Text to analyze: {paragraph}`
  },
  'market_risk': {
    name: 'Market Risk Analysis',
    template: `Analyze the following text for market risk indicators. Return a JSON response with this exact structure:
{
  "risk_type": "Market Risk",
  "severity": "High/Medium/Low", 
  "summary": "Brief summary of market risk findings",
  "key_findings": ["finding1", "finding2", "finding3"],
  "recommendations": ["recommendation1", "recommendation2"]
}

Text to analyze: {paragraph}`
  },
  'operational_risk': {
    name: 'Operational Risk Analysis',
    template: `Analyze the following text for operational risk indicators. Return a JSON response with this exact structure:
{
  "risk_type": "Operational Risk",
  "severity": "High/Medium/Low",
  "summary": "Brief summary of operational risk findings", 
  "key_findings": ["finding1", "finding2", "finding3"],
  "recommendations": ["recommendation1", "recommendation2"]
}

Text to analyze: {paragraph}`
  },
  'liquidity_risk': {
    name: 'Liquidity Risk Analysis',
    template: `Analyze the following text for liquidity risk indicators. Return a JSON response with this exact structure:
{
  "risk_type": "Liquidity Risk",
  "severity": "High/Medium/Low",
  "summary": "Brief summary of liquidity risk findings",
  "key_findings": ["finding1", "finding2", "finding3"], 
  "recommendations": ["recommendation1", "recommendation2"]
}

Text to analyze: {paragraph}`
  }
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { document, prompts }: RiskAnalysisRequest = await req.json();
    
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
      .slice(0, 5); // Limit to first 5 paragraphs for efficiency

    for (const promptKey of prompts) {
      const promptTemplate = PROMPT_TEMPLATES[promptKey as keyof typeof PROMPT_TEMPLATES];
      
      if (!promptTemplate) {
        console.warn(`Prompt template not found: ${promptKey}`);
        continue;
      }

      for (const paragraph of paragraphs) {
        try {
          const prompt = promptTemplate.template.replace('{paragraph}', paragraph);
          
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
            console.error(`OpenAI API error: ${response.status} ${response.statusText}`);
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