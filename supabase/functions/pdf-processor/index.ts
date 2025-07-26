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
    
    // Improved text extraction approach
    try {
      const pdfBytes = new Uint8Array(buffer);
      const pdfString = decoder.decode(pdfBytes);
      
      // Extract text using multiple strategies for better paragraph detection
      
      // Strategy 1: Extract from parentheses (most common in PDFs)
      const textRegex = /\(((?:[^()\\]|\\.)*)\)/g;
      const textMatches = [];
      let match;
      
      while ((match = textRegex.exec(pdfString)) !== null) {
        const text = match[1]
          .replace(/\\([()\\])/g, '$1') // Unescape special characters
          .replace(/\\n/g, '\n') // Handle explicit newlines
          .replace(/\\r/g, '\r') // Handle carriage returns
          .replace(/\\t/g, '\t'); // Handle tabs
        
        if (text.length > 1) {
          textMatches.push(text);
        }
      }
      
      if (textMatches.length > 0) {
        // Reconstruct paragraphs by analyzing text patterns
        let reconstructedText = '';
        let currentParagraph = '';
        
        for (let i = 0; i < textMatches.length; i++) {
          const text = textMatches[i].trim();
          
          if (!text) continue;
          
          // Check if this looks like a continuation of the previous text
          const nextText = textMatches[i + 1]?.trim() || '';
          const isEndOfSentence = /[.!?]\s*$/.test(text);
          const isNewParagraph = /^[A-Z]/.test(nextText) && isEndOfSentence;
          const isListItem = /^[\d•\-\*]\s/.test(text);
          
          currentParagraph += text;
          
          // Add space if the current text doesn't end with punctuation and next text exists
          if (nextText && !text.endsWith(' ') && !/[.!?;:,]\s*$/.test(text)) {
            currentParagraph += ' ';
          }
          
          // Start new paragraph if:
          // 1. Current text ends with sentence punctuation and next starts with capital
          // 2. Current text is a list item
          // 3. Significant content change detected
          if (isNewParagraph || isListItem || i === textMatches.length - 1) {
            if (currentParagraph.trim()) {
              reconstructedText += currentParagraph.trim() + '\n\n';
              currentParagraph = '';
            }
          }
        }
        
        fullText = reconstructedText;
      }
      
      // Strategy 2: Fallback to TJ arrays if previous method failed
      if (!fullText.trim()) {
        const tjRegex = /\[((?:[^\[\]\\]|\\.)*)\]\s*TJ/g;
        const tjMatches = [];
        
        while ((match = tjRegex.exec(pdfString)) !== null) {
          const content = match[1];
          // Parse array content
          const textParts = content.match(/\(((?:[^()\\]|\\.)*)\)/g);
          if (textParts) {
            const text = textParts.map(part => 
              part.slice(1, -1).replace(/\\([()\\])/g, '$1')
            ).join('');
            
            if (text.trim().length > 2) {
              tjMatches.push(text);
            }
          }
        }
        
        if (tjMatches.length > 0) {
          fullText = tjMatches.join(' ');
        }
      }
      
    } catch (textError) {
      console.warn('Text extraction failed:', textError);
      
      // Ultimate fallback: extract readable sequences
      const pdfBytes = new Uint8Array(buffer);
      const readableTextRegex = /[A-Za-z][A-Za-z\s.,!?;:'"()-]{10,}/g;
      const readableMatches = decoder.decode(pdfBytes).match(readableTextRegex);
      
      if (readableMatches) {
        fullText = readableMatches
          .filter(text => text.length > 10)
          .join(' ');
      }
    }
    
    // Final text cleanup and paragraph formatting
    fullText = fullText
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/([.!?])\s+([A-Z])/g, '$1\n\n$2') // Add paragraph breaks after sentences
      .replace(/\n{3,}/g, '\n\n') // Normalize paragraph breaks
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
    console.log('PDF Processor function called with method:', req.method);
    console.log('Headers:', Object.fromEntries(req.headers.entries()));
    
    if (req.method !== 'POST') {
      console.error('Invalid method:', req.method);
      throw new Error('Method not allowed');
    }

    let formData;
    try {
      formData = await req.formData();
      console.log('FormData received successfully');
    } catch (formError) {
      console.error('Failed to parse FormData:', formError);
      throw new Error(`Failed to parse form data: ${formError.message}`);
    }

    const file = formData.get('file') as File;
    const documentId = formData.get('document_id') as string;
    const companyName = formData.get('company_name') as string;

    console.log('Form fields received:', {
      hasFile: !!file,
      fileSize: file?.size,
      fileName: file?.name,
      fileType: file?.type,
      documentId,
      companyName
    });

    if (!file || !documentId || !companyName) {
      console.error('Missing required fields:', { file: !!file, documentId, companyName });
      throw new Error('Missing required fields: file, document_id, or company_name');
    }

    console.log(`Processing PDF: ${file.name} (${file.size} bytes) for ${companyName}`);

    // Convert file to array buffer
    let arrayBuffer;
    try {
      arrayBuffer = await file.arrayBuffer();
      console.log('Successfully converted file to ArrayBuffer, size:', arrayBuffer.byteLength);
    } catch (bufferError) {
      console.error('Failed to convert file to ArrayBuffer:', bufferError);
      throw new Error(`Failed to read file: ${bufferError.message}`);
    }
    
    // Extract text using our custom function
    console.log('Starting text extraction...');
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
      content: fullText.substring(0, 50000), // Limit content size to prevent JSON issues
      text: fullText.substring(0, 50000), // Limit text size to prevent JSON issues
      paragraphs: paragraphs.slice(0, 100), // Limit paragraphs to prevent response size issues
      processed: true
    };

    console.log('Preparing response with result:', {
      document_id: result.document_id,
      company_name: result.company_name,
      file_name: result.file_name,
      contentLength: result.content.length,
      textLength: result.text.length,
      paragraphsCount: result.paragraphs.length,
      processed: result.processed
    });

    try {
      const responseJson = JSON.stringify(result);
      console.log('Response JSON created successfully, size:', responseJson.length);
      
      return new Response(responseJson, {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    } catch (jsonError) {
      console.error('Failed to stringify result:', jsonError);
      
      // Return a simplified result if JSON.stringify fails
      const simplifiedResult = {
        document_id: documentId,
        company_name: companyName,
        file_name: file.name,
        content: 'Content too large for response',
        text: 'Text too large for response',
        paragraphs: [],
        processed: true
      };
      
      return new Response(JSON.stringify(simplifiedResult), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

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