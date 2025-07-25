import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.52.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// PDF.js library for server-side PDF processing
import * as pdfjsLib from 'https://esm.sh/pdfjs-dist@4.0.379/legacy/build/pdf.mjs';

// Disable worker for server-side processing
(pdfjsLib as any).GlobalWorkerOptions.workerSrc = false;

interface PDFChunk {
  text: string;
  page: number;
  metadata: {
    company: string;
  };
}

interface ProcessingResult {
  document_id: string;
  company_name: string;
  file_name: string;
  content: string;
  text: string;
  paragraphs: PDFChunk[];
  processed: boolean;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('PDF Processor function called');
    
    if (req.method !== 'POST') {
      throw new Error('Method not allowed');
    }

    const formData = await req.formData();
    const file = formData.get('file') as File;
    const documentId = formData.get('document_id') as string;
    const companyName = formData.get('company_name') as string;

    if (!file || !documentId || !companyName) {
      throw new Error('Missing required fields: file, document_id, or company_name');
    }

    console.log(`Processing PDF: ${file.name} for ${companyName}`);

    // Risk keywords similar to Python version
    const riskKeywords = [
      'risk', 'uncertainty', 'threat', 'challenge', 'exposure',
      'volatility', 'fluctuation', 'adverse', 'decline', 'loss',
      'default', 'credit', 'market', 'operational', 'liquidity'
    ];

    // Convert file to array buffer
    const arrayBuffer = await file.arrayBuffer();
    
    // Process PDF with PDF.js
    const loadingTask = pdfjsLib.getDocument(new Uint8Array(arrayBuffer));
    const pdf = await loadingTask.promise;
    
    console.log(`PDF loaded with ${pdf.numPages} pages`);

    let fullText = '';
    
    // Extract text from all pages
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item: any) => item.str)
        .join(' ');
      
      fullText += pageText + '\n';
    }

    // Chunk text similar to Python version
    const chunkText = (text: string, chunkSize: number = 1000, overlap: number = 200): string[] => {
      const chunks: string[] = [];
      let start = 0;

      while (start < text.length) {
        const end = Math.min(start + chunkSize, text.length);
        chunks.push(text.slice(start, end));
        start += chunkSize - overlap;
      }

      return chunks;
    };

    const chunks = chunkText(fullText);
    const paragraphs: PDFChunk[] = [];

    // Filter chunks for risk-related content
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      
      // Check if chunk contains risk-related keywords
      const hasRiskKeyword = riskKeywords.some(keyword => 
        chunk.toLowerCase().includes(keyword.toLowerCase())
      );

      if (hasRiskKeyword && chunk.trim().length > 50) {
        paragraphs.push({
          text: chunk.trim(),
          page: Math.floor((i / chunks.length) * pdf.numPages) + 1,
          metadata: { company: companyName }
        });
      }
    }

    console.log(`Found ${paragraphs.length} risk-related paragraphs`);

    const result: ProcessingResult = {
      document_id: documentId,
      company_name: companyName,
      file_name: file.name,
      content: fullText,
      text: fullText,
      paragraphs,
      processed: true
    };

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Store processed data in Supabase storage or database if needed
    // For now, just return the result

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in pdf-processor function:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message,
        details: 'PDF processing failed'
      }), 
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});