import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { useAuth } from '@/hooks/useAuth'
import { usePDFProcessor } from '@/hooks/usePDFProcessor'
import { useDocuments } from '@/hooks/useDocuments'
import toast from 'react-hot-toast'
import { Upload, FileText, AlertCircle, CheckCircle2 } from 'lucide-react'

const UploadDocument = () => {
  const { user } = useAuth()
  const { processPDF, processing, progress } = usePDFProcessor()
  const { saveDocument } = useDocuments()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    file: null as File | null,
    document_id: '',
    company_name: ''
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setFormData(prev => ({
        ...prev,
        file,
        document_id: prev.document_id || `doc_${Date.now()}`
      }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.file || !formData.document_id || !formData.company_name) {
      toast.error('请填写所有字段并选择文件')
      return
    }

    // Check if file is PDF
    if (formData.file.type !== 'application/pdf') {
      toast.error('目前只支持PDF文件处理')
      return
    }

    setLoading(true)
    
    try {
      // Process PDF directly in frontend
      await handlePDFProcessing()
      resetForm()
    } catch (error) {
      console.error('PDF处理错误:', error)
      toast.error(error instanceof Error ? error.message : 'PDF处理失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePDFProcessing = async () => {
    if (!user) {
      throw new Error('User not authenticated')
    }

    try {
      toast.success('开始处理PDF文档...')
      
      const result = await processPDF(
        formData.file!,
        formData.document_id,
        formData.company_name
      )

      // Store processed result in Supabase database
      await saveDocument({
        document_id: formData.document_id,
        company_name: formData.company_name,
        file_name: formData.file?.name || 'unknown.pdf',
        content: result.content,
        text_content: result.text,
        paragraphs: result.paragraphs
      })
      
      toast.success(`PDF处理完成！提取了 ${result.paragraphs?.length || 0} 个风险相关段落`)
      console.log('PDF处理结果:', result)
    } catch (error) {
      console.error('PDF处理错误:', error)
      throw error
    }
  }


  const resetForm = () => {
    setFormData({ file: null, document_id: '', company_name: '' })
    
    // Reset file input
    const fileInput = document.getElementById('file') as HTMLInputElement
    if (fileInput) fileInput.value = ''
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Upload Document</h1>
        <p className="text-muted-foreground">
          Upload financial documents for risk analysis
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Upload className="h-5 w-5" />
            <span>Document Upload</span>
          </CardTitle>
          <CardDescription>
            Select a financial document to upload and analyze
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="file">Document File</Label>
              <Input
                id="file"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="cursor-pointer"
              />
              <p className="text-xs text-muted-foreground">
                目前支持PDF格式，将自动提取风险相关内容
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="document_id">Document ID</Label>
              <Input
                id="document_id"
                value={formData.document_id}
                onChange={(e) => setFormData(prev => ({ ...prev, document_id: e.target.value }))}
                placeholder="Enter unique document identifier"
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="company_name">Company Name</Label>
              <Input
                id="company_name"
                value={formData.company_name}
                onChange={(e) => setFormData(prev => ({ ...prev, company_name: e.target.value }))}
                placeholder="Enter company name"
                className="w-full"
              />
            </div>

            {(processing || loading) && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  {progress.stage === 'complete' ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-blue-500 animate-pulse" />
                  )}
                  <span className="text-sm font-medium">
                    {progress.stage === 'parsing' && 'PDF解析中...'}
                    {progress.stage === 'chunking' && '文本分割中...'}
                    {progress.stage === 'filtering' && '风险段落筛选中...'}
                    {progress.stage === 'complete' && 'PDF处理完成!'}
                  </span>
                </div>
                
                <Progress value={progress.progress} className="w-full" />
                
                <div className="text-xs text-muted-foreground">
                  {progress.stage === 'parsing' && `解析进度: ${progress.progress}%`}
                  {progress.stage === 'chunking' && `分割进度: ${progress.progress}% ${progress.totalPages ? `(${progress.totalPages}页)` : ''}`}
                  {progress.stage === 'filtering' && `筛选进度: ${progress.progress}% ${progress.chunksProcessed && progress.totalChunks ? `(${progress.chunksProcessed}/${progress.totalChunks} 块)` : ''}`}
                  {progress.stage === 'complete' && '所有处理步骤已完成'}
                </div>
              </div>
            )}

            <Button 
              type="submit" 
              disabled={loading || processing}
              className="w-full flex items-center space-x-2"
            >
              <FileText className="h-4 w-4" />
              <span>
                {processing ? 'PDF处理中...' : loading ? '上传中...' : '上传文档'}
              </span>
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Upload Guidelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm space-y-2">
            <p className="font-medium">Supported Document Types:</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>Financial statements (PDF, DOC, DOCX)</li>
              <li>Risk assessment reports</li>
              <li>Audit documents</li>
              <li>Compliance reports</li>
              <li>Plain text files (TXT)</li>
            </ul>
          </div>
          <div className="text-sm space-y-2">
            <p className="font-medium">Best Practices:</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>Use descriptive document IDs</li>
              <li>Ensure documents are in English</li>
              <li>Maximum file size: 10MB</li>
              <li>Include company name for better organization</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default UploadDocument