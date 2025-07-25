import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import { Upload, FileText } from 'lucide-react'

const UploadDocument = () => {
  const { user } = useAuth()
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
      toast.error('Please fill all fields and select a file')
      return
    }

    setLoading(true)
    
    try {
      // Try to connect to backend first
      const healthCheck = await fetch('http://localhost:8000/health', {
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
      })

      if (healthCheck.ok) {
        // Backend is available, proceed with actual upload
        await handleRealUpload()
        resetForm()
      } else {
        // Backend is not responding properly
        await handleMockUpload()
        resetForm()
      }
    } catch (error) {
      console.error('Backend connection error:', error)
      // Backend is not available, use mock upload
      await handleMockUpload()
      resetForm()
    } finally {
      setLoading(false)
    }
  }

  const handleRealUpload = async () => {
    try {
      // Step 1: Upload document
      const uploadFormData = new FormData()
      uploadFormData.append('file', formData.file!)
      uploadFormData.append('document_id', formData.document_id)
      uploadFormData.append('company_name', formData.company_name)
      uploadFormData.append('user_id', user?.id || 'demo-user')

      const uploadResponse = await fetch('http://localhost:8000/api/documents/upload', {
        method: 'POST',
        body: uploadFormData,
      })

      if (uploadResponse.ok) {
        const uploadResult = await uploadResponse.json()
        toast.success('Document uploaded successfully!')
        
        // Step 2: Process document with pdf_processor
        const processResponse = await fetch(`http://localhost:8000/api/documents/${formData.document_id}/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            document_id: formData.document_id,
            company_name: formData.company_name,
            user_id: user?.id || 'demo-user'
          }),
        })

        if (processResponse.ok) {
          const processResult = await processResponse.json()
          toast.success('Document processed successfully!')
          console.log('Processing result:', processResult)
        } else {
          toast.error('Document uploaded but processing failed')
        }
      } else {
        const errorText = await uploadResponse.text()
        toast.error(`Upload failed: ${errorText}`)
      }
    } catch (error) {
      console.error('Real upload error:', error)
      throw error
    }
  }

  const handleMockUpload = async () => {
    // Simulate upload process
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Mock successful upload and processing
    const mockResult = {
      document_id: formData.document_id,
      company_name: formData.company_name,
      file_name: formData.file?.name,
      paragraphs: [
        {
          text: "Sample risk paragraph extracted from document...",
          page: 1,
          metadata: { company: formData.company_name }
        }
      ],
      processed: true
    }
    
    // Store mock result in localStorage for other components
    localStorage.setItem(`document_${formData.document_id}`, JSON.stringify(mockResult))
    
    toast.success('Document uploaded and processed successfully! (Demo Mode)')
    console.log('Mock processing result:', mockResult)
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
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileChange}
                className="cursor-pointer"
              />
              <p className="text-xs text-muted-foreground">
                Supported formats: PDF, DOC, DOCX, TXT
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

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full flex items-center space-x-2"
            >
              <FileText className="h-4 w-4" />
              <span>{loading ? 'Uploading...' : 'Upload Document'}</span>
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