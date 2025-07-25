import { useState, useCallback } from 'react'
import * as pdfjsLib from 'pdfjs-dist'

// 设置PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

interface PDFChunk {
  text: string
  page: number
  metadata: {
    company: string
  }
}

interface ProcessingProgress {
  stage: 'parsing' | 'chunking' | 'filtering' | 'complete'
  progress: number
  currentPage?: number
  totalPages?: number
  chunksProcessed?: number
  totalChunks?: number
}

interface PDFProcessorResult {
  document_id: string
  company_name: string
  file_name: string
  content: string
  text: string
  paragraphs: PDFChunk[]
  processed: boolean
}

export const usePDFProcessor = () => {
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<ProcessingProgress>({
    stage: 'parsing',
    progress: 0
  })

  const riskKeywords = ['risk', 'uncertainty', 'threat', 'challenge', 'exposure', '风险', '不确定性', '威胁', '挑战']

  const chunkText = (text: string, chunkSize: number = 1000, overlap: number = 200): string[] => {
    const chunks: string[] = []
    let start = 0

    while (start < text.length) {
      const end = Math.min(start + chunkSize, text.length)
      chunks.push(text.slice(start, end))
      start += chunkSize - overlap
    }

    return chunks
  }

  const processDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  const processPDF = useCallback(async (
    file: File,
    documentId: string,
    companyName: string
  ): Promise<PDFProcessorResult> => {
    setProcessing(true)
    setProgress({ stage: 'parsing', progress: 0 })

    try {
      // Stage 1: Parse PDF
      setProgress({ stage: 'parsing', progress: 0 })
      
      const arrayBuffer = await file.arrayBuffer()
      const loadingTask = pdfjsLib.getDocument(arrayBuffer)
      const pdf = await loadingTask.promise
      
      setProgress({ 
        stage: 'parsing', 
        progress: 50,
        totalPages: pdf.numPages 
      })

      // Stage 2: Extract text from all pages
      setProgress({ 
        stage: 'chunking', 
        progress: 0,
        totalPages: pdf.numPages 
      })

      let fullText = ''
      
      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum)
        const textContent = await page.getTextContent()
        const pageText = textContent.items
          .map((item: any) => item.str)
          .join(' ')
        
        fullText += pageText + '\n'
        
        // Update progress
        const progress = Math.round((pageNum / pdf.numPages) * 100)
        setProgress({ 
          stage: 'chunking', 
          progress,
          currentPage: pageNum,
          totalPages: pdf.numPages 
        })
        
        // Add small delay to show progress
        await processDelay(50)
      }

      
      // Stage 3: Chunk the full text
      const chunks = chunkText(fullText)
      
      // Stage 4: Filter and create paragraphs

      setProgress({ 
        stage: 'filtering', 
        progress: 0,
        totalChunks: chunks.length 
      })

      const paragraphs: PDFChunk[] = []
      
      for (let i = 0; i < chunks.length; i++) {
        const chunk = chunks[i]
        
        // Check if chunk contains risk-related keywords
        const hasRiskKeyword = riskKeywords.some(keyword => 
          chunk.toLowerCase().includes(keyword.toLowerCase())
        )

        if (hasRiskKeyword && chunk.trim().length > 50) {
          paragraphs.push({
            text: chunk.trim(),
            page: Math.floor((i / chunks.length) * pdf.numPages) + 1,
            metadata: { company: companyName }
          })
        }

        // Update progress
        const progress = Math.round(((i + 1) / chunks.length) * 100)
        setProgress({ 
          stage: 'filtering', 
          progress,
          chunksProcessed: i + 1,
          totalChunks: chunks.length 
        })
        
        // Add small delay every 10 chunks to show progress
        if (i % 10 === 0) {
          await processDelay(50)
        }
      }

      setProgress({ stage: 'complete', progress: 100 })
      await processDelay(200)

      const result: PDFProcessorResult = {
        document_id: documentId,
        company_name: companyName,
        file_name: file.name,
        content: fullText,
        text: fullText,
        paragraphs,
        processed: true
      }

      return result

    } catch (error) {
      console.error('PDF处理错误:', error)
      throw new Error(`PDF处理失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setProcessing(false)
    }
  }, [])

  return {
    processPDF,
    processing,
    progress
  }
}