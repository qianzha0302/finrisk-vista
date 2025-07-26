import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface RAGQueryRequest {
  document_id: string;
  question: string;
  conversation_history?: Array<{role: string, content: string}>;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { document_id, question, conversation_history }: RAGQueryRequest = await req.json();

    if (!document_id || !question) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: document_id and question' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    console.log(`🔍 Processing RAG query for document: ${document_id}`);
    console.log(`❓ Question: ${question}`);

    // Get the document from database to verify it exists
    const { data: document, error: docError } = await supabase
      .from('processed_documents')
      .select('*')
      .eq('document_id', document_id)
      .single();

    if (docError || !document) {
      console.error('Document not found:', docError);
      return new Response(
        JSON.stringify({ error: 'Document not found or not processed yet' }),
        { 
          status: 404, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Prepare the RAG query using OpenAI
    const openAIApiKey = Deno.env.get('OPENAI_API_KEY');
    if (!openAIApiKey) {
      return new Response(
        JSON.stringify({ error: 'OpenAI API key not configured' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Extract relevant paragraphs from the document
    const paragraphs = document.paragraphs || [];
    if (!Array.isArray(paragraphs) || paragraphs.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No paragraphs found in document' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Simple keyword-based relevance scoring for RAG
    const scoreParagraph = (paragraph: any, query: string): number => {
      const content = paragraph.content || '';
      const queryWords = query.toLowerCase().split(' ').filter(w => w.length > 2);
      const contentLower = content.toLowerCase();
      
      let score = 0;
      for (const word of queryWords) {
        if (contentLower.includes(word)) {
          score += 1;
        }
      }
      
      // Boost score for financial and risk-related content
      const riskKeywords = ['risk', 'threat', 'exposure', 'uncertainty', 'adverse'];
      const financialKeywords = ['revenue', 'profit', 'loss', 'assets', 'liabilities'];
      
      for (const keyword of riskKeywords) {
        if (contentLower.includes(keyword)) score += 2;
      }
      
      for (const keyword of financialKeywords) {
        if (contentLower.includes(keyword)) score += 1.5;
      }
      
      return score / content.length * 1000; // Normalize by length
    };

    // Get top relevant paragraphs
    const scoredParagraphs = paragraphs
      .map((p: any) => ({
        ...p,
        relevance_score: scoreParagraph(p, question)
      }))
      .filter((p: any) => p.relevance_score > 0)
      .sort((a: any, b: any) => b.relevance_score - a.relevance_score)
      .slice(0, 5); // Take top 5 most relevant

    console.log(`📋 Found ${scoredParagraphs.length} relevant paragraphs`);

    if (scoredParagraphs.length === 0) {
      return new Response(
        JSON.stringify({
          query: question,
          answer: "I couldn't find any relevant information in the document to answer your question.",
          confidence_score: 0,
          relevant_paragraphs: [],
          document_id: document_id
        }),
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Prepare context for OpenAI
    const context = scoredParagraphs
      .map((p: any, index: number) => `[段落 ${index + 1}]: ${p.content}`)
      .join('\n\n');

    // Build conversation messages
    const messages = [
      {
        role: 'system',
        content: `You are a financial document analysis expert. Answer questions based ONLY on the provided document context. 
        
Guidelines:
- Provide accurate, specific answers based on the document content
- If information is not in the context, clearly state that
- Cite specific sections when possible
- Focus on financial risks, compliance, and regulatory matters when relevant
- Be concise but comprehensive
- Answer in the same language as the question`
      }
    ];

    // Add conversation history if provided
    if (conversation_history && Array.isArray(conversation_history)) {
      for (const msg of conversation_history.slice(-4)) { // Last 4 messages for context
        if (msg.role && msg.content) {
          messages.push({
            role: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content
          });
        }
      }
    }

    // Add current question with context
    messages.push({
      role: 'user',
      content: `Based on the following document excerpts, please answer this question: "${question}"

Document Context:
${context}

Question: ${question}`
    });

    // Call OpenAI API
    const openAIResponse = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openAIApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4.1-2025-04-14',
        messages: messages,
        temperature: 0.1,
        max_tokens: 1000,
      }),
    });

    if (!openAIResponse.ok) {
      const errorText = await openAIResponse.text();
      console.error('OpenAI API error:', errorText);
      throw new Error(`OpenAI API error: ${openAIResponse.status}`);
    }

    const aiResult = await openAIResponse.json();
    const answer = aiResult.choices[0]?.message?.content || 'Unable to generate answer';

    // Calculate confidence score based on relevance
    const avgRelevance = scoredParagraphs.reduce((sum: number, p: any) => sum + p.relevance_score, 0) / scoredParagraphs.length;
    const confidence_score = Math.min(avgRelevance * 0.1, 1.0);

    console.log(`✅ RAG query completed successfully`);

    // Return the RAG response
    return new Response(
      JSON.stringify({
        query: question,
        answer: answer,
        confidence_score: confidence_score,
        relevant_paragraphs: scoredParagraphs.map((p: any) => ({
          content: p.content.substring(0, 200) + '...',
          metadata: p.metadata,
          relevance_score: p.relevance_score
        })),
        document_id: document_id,
        processing_time: Date.now(),
        documents_retrieved: scoredParagraphs.length
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );

  } catch (error) {
    console.error('Error in RAG query function:', error);
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error', 
        details: error.message 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});