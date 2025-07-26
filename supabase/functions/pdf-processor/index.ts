import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.52.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Import PDF processing library compatible with Deno
import { getDocument } from 'https://esm.sh/pdfjs-dist@4.8.69/legacy/build/pdf.mjs';
import 'https://esm.sh/pdfjs-dist@4.8.69/legacy/build/pdf.worker.mjs';

async function extractTextFromPDF(buffer: ArrayBuffer): Promise<{ text: string; numPages: number }> {
  try {
    console.log('Processing PDF buffer of size:', buffer.byteLength);
    
    // Load PDF document using pdf.js
    const typedArray = new Uint8Array(buffer);
    const loadingTask = getDocument({ data: typedArray, disableFontFace: true });
    const pdfDoc = await loadingTask.promise;
    const numPages = pdfDoc.numPages;
    
    console.log(`PDF loaded with ${numPages} pages`);
    
    let fullText = '';
    
    // Extract text from each page
    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      try {
        const page = await pdfDoc.getPage(pageNum);
        const textContent = await page.getTextContent();
        
        // Extract text items and reconstruct paragraphs
        const textItems = textContent.items;
        let pageText = '';
        let currentLine = '';
        let lastY = null;
        let lastX = null;
        
        for (const item of textItems) {
          if ('str' in item && 'transform' in item) {
            const text = item.str;
            const x = item.transform[4];
            const y = item.transform[5];
            
            // Check if this is a new line based on Y coordinate
            if (lastY !== null && Math.abs(y - lastY) > 5) {
              // New line detected
              if (currentLine.trim()) {
                pageText += currentLine.trim() + '\n';
                currentLine = '';
              }
            }
            // Check for significant horizontal gap (new column or section)
            else if (lastX !== null && x - lastX > 20) {
              currentLine += ' ';
            }
            
            currentLine += text + ' ';
            lastY = y;
            lastX = x + (item.width || 0);
          }
        }
        
        // Add remaining text
        if (currentLine.trim()) {
          pageText += currentLine.trim() + '\n';
        }
        
        // Add page break marker
        fullText += pageText + '\n\n';
        
        console.log(`Extracted text from page ${pageNum}: ${pageText.length} characters`);
        
      } catch (pageError) {
        console.warn(`Failed to extract text from page ${pageNum}:`, pageError);
      }
    }
    
    // Clean up the extracted text
    fullText = fullText
      .replace(/\n{3,}/g, '\n\n') // Normalize paragraph breaks
      .replace(/[ \t]+/g, ' ') // Normalize spaces
      .replace(/\n /g, '\n') // Remove spaces at line start
      .replace(/ \n/g, '\n') // Remove spaces at line end
      .trim();
    
    if (!fullText) {
      throw new Error('No text could be extracted from the PDF');
    }
    
    console.log(`Successfully extracted ${fullText.length} characters of text`);
    
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

    // Convert file to array buffer
    const arrayBuffer = await file.arrayBuffer();
    
    // Extract text using our custom function
    const { text: fullText, numPages } = await extractTextFromPDF(arrayBuffer);
    
    console.log(`PDF processed with ${numPages} pages`);

    // Chunk text - process entire document, not just risk-related content
    const chunkText = (text: string, chunkSize: number = 1000, overlap: number = 200): string[] => {
      const chunks: string[] = [];
      let start = 0;

      while (start < text.length) {
        const end = Math.min(start + chunkSize, text.length);
        const chunk = text.slice(start, end);
        
        // Only add chunks that have meaningful content
        if (chunk.trim().length > 50) {
          chunks.push(chunk.trim());
        }
        
        start += chunkSize - overlap;
      }

      return chunks;
    };

    const chunks = chunkText(fullText);
    const paragraphs: PDFChunk[] = [];

    // Convert all chunks to paragraphs (not just risk-related ones)
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      
      paragraphs.push({
        text: chunk,
        page: Math.floor((i / chunks.length) * numPages) + 1,
        metadata: { company: companyName }
      });
    }

    console.log(`Created ${paragraphs.length} text chunks from ${numPages} pages`);

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