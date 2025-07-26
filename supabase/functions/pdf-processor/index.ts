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
    
    // Try to extract text using a simpler, more reliable approach
    try {
      const pdfBytes = new Uint8Array(buffer);
      const pdfString = new TextDecoder('utf-8', { fatal: false }).decode(pdfBytes);
      
      // Look for text content between 'BT' and 'ET' operators (text objects)
      const textObjectRegex = /BT\s+([\s\S]*?)\s+ET/g;
      const textObjects = [];
      let match;
      
      while ((match = textObjectRegex.exec(pdfString)) !== null) {
        const textObject = match[1];
        
        // Extract text from Tj operators (show text)
        const tjRegex = /\(((?:[^()\\]|\\[\\()nrtbf]|\\[0-7]{1,3})*)\)\s*Tj/g;
        let textMatch;
        
        while ((textMatch = tjRegex.exec(textObject)) !== null) {
          let text = textMatch[1];
          
          // Decode escape sequences
          text = text
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\r')
            .replace(/\\t/g, '\t')
            .replace(/\\b/g, '\b')
            .replace(/\\f/g, '\f')
            .replace(/\\([\\()])/g, '$1')
            .replace(/\\([0-7]{1,3})/g, (_, octal) => String.fromCharCode(parseInt(octal, 8)));
          
          // Only include text that looks like readable content
          if (text.length > 2 && /[a-zA-Z0-9]/.test(text)) {
            textObjects.push(text);
          }
        }
        
        // Also try TJ operators (show text with individual glyph positioning)
        const tjArrayRegex = /\[((?:[^\[\]\\]|\\[\\()nrtbf]|\\[0-7]{1,3})*)\]\s*TJ/g;
        
        while ((textMatch = tjArrayRegex.exec(textObject)) !== null) {
          const arrayContent = textMatch[1];
          
          // Extract strings from the array
          const stringRegex = /\(((?:[^()\\]|\\[\\()nrtbf]|\\[0-7]{1,3})*)\)/g;
          let stringMatch;
          
          while ((stringMatch = stringRegex.exec(arrayContent)) !== null) {
            let text = stringMatch[1];
            
            text = text
              .replace(/\\n/g, '\n')
              .replace(/\\r/g, '\r')
              .replace(/\\t/g, '\t')
              .replace(/\\b/g, '\b')
              .replace(/\\f/g, '\f')
              .replace(/\\([\\()])/g, '$1')
              .replace(/\\([0-7]{1,3})/g, (_, octal) => String.fromCharCode(parseInt(octal, 8)));
            
            if (text.length > 2 && /[a-zA-Z0-9]/.test(text)) {
              textObjects.push(text);
            }
          }
        }
      }
      
      if (textObjects.length > 0) {
        // Join text objects with appropriate spacing
        fullText = textObjects.join(' ');
      }
      
      // If that didn't work, try a more comprehensive approach
      if (!fullText.trim() || fullText.length < 100) {
        console.log('First extraction method failed, trying alternative approach');
        
        // Look for any parentheses-enclosed strings that might be text
        const allTextRegex = /\(([^()]*(?:\\.[^()]*)*)\)/g;
        const allTexts = [];
        
        while ((match = allTextRegex.exec(pdfString)) !== null) {
          let text = match[1];
          
          // Decode basic escape sequences
          text = text
            .replace(/\\n/g, ' ')
            .replace(/\\r/g, ' ')
            .replace(/\\t/g, ' ')
            .replace(/\\([\\()])/g, '$1');
          
          // Filter for likely text content
          if (text.length > 1 && /[a-zA-Z]/.test(text)) {
            allTexts.push(text);
          }
        }
        
        if (allTexts.length > 0) {
          fullText = allTexts.join(' ');
        }
      }
      
    } catch (extractError) {
      console.error('Text extraction error:', extractError);
      throw new Error('Failed to extract readable text from PDF');
    }
    
    // Clean up the extracted text
    if (fullText) {
      fullText = fullText
        // Remove control characters and non-printable characters except common whitespace
        .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]/g, ' ')
        // Keep only ASCII printable characters and common Unicode
        .replace(/[^\x20-\x7E\u00A0-\u024F\u1E00-\u1EFF\s]/g, ' ')
        // Normalize whitespace
        .replace(/\s+/g, ' ')
        // Try to reconstruct sentences
        .replace(/([a-z])\s+([A-Z])/g, '$1. $2')
        .trim();
    }
    
    if (!fullText || fullText.length < 50) {
      throw new Error('No meaningful text could be extracted from the PDF');
    }
    
    console.log(`Successfully extracted ${fullText.length} characters of readable text`);
    
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