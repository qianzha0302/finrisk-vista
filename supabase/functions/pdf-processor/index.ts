import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Financial keywords to filter for relevant sections
const FINANCIAL_KEYWORDS = [
  "risk factors", "item 1a", "item 7", "management's discussion", 
  "footnotes", "note", "md&a", "risk management", "credit risk",
  "market risk", "operational risk", "liquidity risk", "capital",
  "derivatives", "trading", "investment", "regulatory", "compliance"
];

interface PageText {
  pageNum: number;
  content: string;
}

// Simple text extraction using basic string methods (more reliable than PDF.js in edge functions)
async function extractTextFromPDF(buffer: ArrayBuffer): Promise<{ pages: PageText[]; numPages: number }> {
  try {
    console.log('Processing PDF buffer of size:', buffer.byteLength);
    
    // Convert buffer to string and look for text patterns
    const uint8Array = new Uint8Array(buffer);
    let text = '';
    
    // Simple extraction - look for readable text between PDF markers
    for (let i = 0; i < uint8Array.length - 1; i++) {
      const char = uint8Array[i];
      // Only include printable ASCII characters and common punctuation
      if ((char >= 32 && char <= 126) || char === 10 || char === 13) {
        text += String.fromCharCode(char);
      } else if (char === 0) {
        text += ' '; // Replace null bytes with spaces
      }
    }
    
    // Clean up the extracted text
    text = text
      .replace(/\0/g, ' ')           // Remove null bytes
      .replace(/[\x00-\x1F\x7F-\x9F]/g, ' ') // Remove control characters
      .replace(/\s+/g, ' ')          // Normalize whitespace
      .trim();
    
    console.log('Extracted text length:', text.length);
    
    if (text.length < 100) {
      throw new Error('Could not extract meaningful text from PDF');
    }
    
    // Split text into chunks that represent "pages" (approximate)
    const avgPageLength = 2000;
    const pages: PageText[] = [];
    
    for (let i = 0; i < text.length; i += avgPageLength) {
      const pageContent = text.slice(i, i + avgPageLength);
      if (pageContent.trim().length > 50) {
        pages.push({
          pageNum: Math.floor(i / avgPageLength) + 1,
          content: pageContent.trim()
        });
      }
    }
    
    console.log(`Successfully extracted text from ${pages.length} page chunks`);
    return { pages, numPages: pages.length };
    
  } catch (error) {
    console.error('Error extracting text from PDF:', error);
    throw new Error(`PDF processing failed: ${error.message}`);
  }
}


function filterRelevantPages(pages: PageText[]): PageText[] {
  console.log('Filtering pages for financial content...');
  
  const relevantPages = pages.filter(page => {
    const content = page.content.toLowerCase();
    return FINANCIAL_KEYWORDS.some(keyword => content.includes(keyword.toLowerCase()));
  });
  
  console.log(`Found ${relevantPages.length} relevant pages out of ${pages.length} total pages`);
  return relevantPages;
}

function chunkText(text: string, chunkSize: number = 800, overlap: number = 150): string[] {
  const chunks: string[] = [];
  
  if (text.length <= chunkSize) {
    return [text];
  }
  
  let start = 0;
  
  while (start < text.length) {
    let end = start + chunkSize;
    
    // If we're not at the end of the text, try to break at a sentence boundary
    if (end < text.length) {
      const lastSentenceEnd = text.lastIndexOf('.', end);
      const lastQuestionEnd = text.lastIndexOf('?', end);
      const lastExclamationEnd = text.lastIndexOf('!', end);
      
      const sentenceEnd = Math.max(lastSentenceEnd, lastQuestionEnd, lastExclamationEnd);
      
      if (sentenceEnd > start + chunkSize / 2) {
        end = sentenceEnd + 1;
      }
    }
    
    const chunk = text.slice(start, end).trim();
    if (chunk.length > 50) {
      chunks.push(chunk);
    }
    
    // Move start position with overlap
    start = Math.max(start + chunkSize - overlap, end - overlap);
    
    // Prevent infinite loop
    if (start >= text.length - overlap) {
      break;
    }
  }
  
  return chunks.filter(chunk => chunk.length > 50);
}

function identifySection(content: string): string {
  const sectionPatterns = [
    { pattern: /Item\s+1A\.?\s+Risk Factors/i, name: 'Risk Factors' },
    { pattern: /Management's Discussion and Analysis/i, name: 'MD&A' },
    { pattern: /Financial Statements/i, name: 'Financial Statements' },
    { pattern: /Item\s+8\.?\s+Financial Statements/i, name: 'Financial Statements' },
    { pattern: /Item\s+7\.?\s+/i, name: 'MD&A' },
    { pattern: /footnotes?/i, name: 'Footnotes' },
    { pattern: /notes? to /i, name: 'Notes' }
  ];
  
  for (const { pattern, name } of sectionPatterns) {
    if (pattern.test(content)) {
      return name;
    }
  }
  
  return 'General';
}

interface PDFChunk {
  text: string;
  page: number;
  metadata: {
    company: string;
    section_name: string;
    page_number: number;
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
    
    // Extract text using PDF.js
    console.log('Starting text extraction...');
    const { pages, numPages } = await extractTextFromPDF(arrayBuffer);
    
    console.log(`PDF processed with ${numPages} pages`);
    
    // Filter for relevant financial sections (like your Streamlit approach)
    const relevantPages = filterRelevantPages(pages);
    
    if (relevantPages.length === 0) {
      console.log('No relevant financial sections found, processing all pages');
      // Fallback to processing all pages if no financial keywords found
      relevantPages.push(...pages.slice(0, 50)); // Limit to first 50 pages to avoid timeout
    }

    const paragraphs: PDFChunk[] = [];
    let allChunks: string[] = [];

    // Process each relevant page and chunk its content
    for (const page of relevantPages) {
      if (page.content.trim().length > 100) { // Only process pages with substantial content
        const pageChunks = chunkText(page.content);
        const sectionName = identifySection(page.content);
        
        // Add chunks with page metadata
        for (const chunk of pageChunks) {
          paragraphs.push({
            text: chunk,
            page: page.pageNum,
            metadata: { 
              company: companyName,
              section_name: sectionName,
              page_number: page.pageNum
            }
          });
        }
        
        allChunks.push(...pageChunks);
      }
    }

    console.log(`Created ${paragraphs.length} useful paragraphs from ${relevantPages.length} relevant pages`);

    // Combine all relevant text for content field
    const combinedText = allChunks.join('\n\n');
    
    const result: ProcessingResult = {
      document_id: documentId,
      company_name: companyName,
      file_name: file.name,
      content: combinedText.substring(0, 50000), // Limit content size to prevent JSON issues
      text: combinedText.substring(0, 50000), // Limit text size to prevent JSON issues
      paragraphs: paragraphs.slice(0, 150), // Increased limit since we're filtering for relevant content
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