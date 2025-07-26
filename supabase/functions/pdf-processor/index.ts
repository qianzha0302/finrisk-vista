import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.52.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Import PDF processing library compatible with Deno
import { PDFDocument } from 'https://esm.sh/pdf-lib@1.17.1';

const decoder = new TextDecoder();

async function extractTextFromPDF(buffer: ArrayBuffer): Promise<{ text: string; numPages: number }> {
  try {
    console.log('Processing PDF buffer of size:', buffer.byteLength);
    
    // Load PDF document
    const pdfDoc = await PDFDocument.load(buffer);
    const pages = pdfDoc.getPages();
    const numPages = pages.length;
    
    console.log(`PDF loaded with ${numPages} pages`);
    
    let fullText = '';
    
    // Extract text from each page
    // Note: pdf-lib doesn't have direct text extraction, so we'll use a different approach
    // We'll try to extract the raw content and parse it
    
    try {
      // Try to extract text using a more manual approach
      const pdfBytes = new Uint8Array(buffer);
      const pdfString = decoder.decode(pdfBytes);
      
      // Look for text objects in PDF content
      const textRegex = /\((.*?)\)/g;
      const textMatches = pdfString.match(textRegex);
      
      if (textMatches) {
        fullText = textMatches
          .map(match => match.slice(1, -1)) // Remove parentheses
          .filter(text => text.length > 2) // Filter out short fragments
          .join(' ');
      }
      
      // If no text found through regex, extract from stream objects
      if (!fullText.trim()) {
        const streamRegex = /stream\s*(.*?)\s*endstream/gs;
        const streamMatches = pdfString.match(streamRegex);
        
        if (streamMatches) {
          for (const stream of streamMatches) {
            const streamContent = stream.replace(/^stream\s*/, '').replace(/\s*endstream$/, '');
            // Look for readable text in streams
            const readableText = streamContent.match(/[a-zA-Z\s]{10,}/g);
            if (readableText) {
              fullText += readableText.join(' ') + ' ';
            }
          }
        }
      }
      
      // If still no text, try to extract from direct text objects
      if (!fullText.trim()) {
        const tjRegex = /\[(.*?)\]\s*TJ/g;
        const tjMatches = pdfString.match(tjRegex);
        
        if (tjMatches) {
          fullText = tjMatches
            .map(match => match.replace(/\[(.*?)\]\s*TJ/, '$1'))
            .join(' ');
        }
      }
      
    } catch (textError) {
      console.warn('Advanced text extraction failed, using fallback:', textError);
      
      // Fallback: extract any readable text from the PDF bytes
      const readableTextRegex = /[A-Za-z]{3,}[\s\w.,!?;:'-]*/g;
      const readableMatches = decoder.decode(pdfBytes).match(readableTextRegex);
      
      if (readableMatches) {
        fullText = readableMatches
          .filter(text => text.length > 5)
          .join(' ');
      }
    }
    
    // Clean up the extracted text
    fullText = fullText
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/[^\w\s.,!?;:'-]/g, ' ') // Remove special characters
      .trim();
    
    if (!fullText) {
      throw new Error('No text could be extracted from the PDF');
    }
    
    console.log(`Extracted ${fullText.length} characters of text`);
    
    return { text: fullText, numPages };
    
  } catch (error) {
    console.error('Error extracting text from PDF:', error);
    throw new Error(`PDF processing failed: ${error.message}`);
  }
}

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
    
    // Extract text using our custom function
    const { text: fullText, numPages } = await extractTextFromPDF(arrayBuffer);
    
    console.log(`PDF processed with ${numPages} pages`);

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
          page: Math.floor((i / chunks.length) * numPages) + 1,
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