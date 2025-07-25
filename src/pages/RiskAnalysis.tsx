import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import { BarChart3, FileText, AlertTriangle } from 'lucide-react'
import RiskVisualization from '@/components/RiskVisualization'
import { supabase } from '@/integrations/supabase/client'

// Available risk analysis prompts matching prompt_registry
const AVAILABLE_PROMPTS = [
  {
    id: 'risk_classifier',
    name: 'Risk Classification',
    description: 'Comprehensive risk categorization and severity assessment'
  },
  {
    id: 'compliance_audit_v2',
    name: 'Compliance Audit',
    description: 'SEC, FINRA, SOX, and Basel regulatory compliance review'
  },
  {
    id: 'esg_risk_v2',
    name: 'ESG Risk Assessment',
    description: 'Environmental, Social, and Governance risk analysis'
  },
  {
    id: 'financial_health_v3',
    name: 'Financial Health Diagnostic',
    description: 'Multi-dimensional financial health and stability assessment'
  },
  {
    id: 'cybersecurity_risk_v2',
    name: 'Cybersecurity Risk',
    description: 'Data security and cyber threat risk evaluation'
  },
  {
    id: 'operational_resilience_v2',
    name: 'Operational Resilience',
    description: 'Business continuity and operational risk assessment'
  }
]

const RiskAnalysis = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>(['risk_classifier'])
  const [result, setResult] = useState<any>(null)
  const [availableDocuments, setAvailableDocuments] = useState<any[]>([])
  const [selectedDocument, setSelectedDocument] = useState<string>('')

  // 加载可用的文档列表
  useEffect(() => {
    const loadDocuments = () => {
      const documents = []
      // 从localStorage获取已上传的文档
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key?.startsWith('document_')) {
          try {
            const docData = JSON.parse(localStorage.getItem(key) || '{}')
            documents.push({
              id: key.replace('document_', ''),
              ...docData
            })
          } catch (error) {
            console.error('Error parsing document data:', error)
          }
        }
      }
      setAvailableDocuments(documents)
      if (documents.length > 0 && !selectedDocument) {
        setSelectedDocument(documents[0].id)
      }
    }

    loadDocuments()
  }, [])

  const togglePrompt = (promptId: string) => {
    setSelectedPrompts(prev => 
      prev.includes(promptId) 
        ? prev.filter(id => id !== promptId)
        : [...prev, promptId]
    )
  }

  const handleAnalysis = async () => {
    if (!selectedDocument || !selectedPrompts.length) {
      toast.error('Please select a document and at least one analysis type')
      return
    }

    setLoading(true)
    
    try {
      // Get document data from localStorage
      const documentData = JSON.parse(localStorage.getItem(`document_${selectedDocument}`) || '{}')
      
      if (!documentData.content && !documentData.text) {
        toast.error('No document content found for analysis')
        setLoading(false)
        return
      }

      console.log('Starting risk analysis for document:', selectedDocument)
      console.log('Selected prompts:', selectedPrompts)
      
      // Call Supabase edge function for risk analysis
      const response = await supabase.functions.invoke('risk-analysis', {
        body: {
          document: {
            id: selectedDocument,
            name: documentData.company_name || 'Unknown Document',
            content: documentData.content || documentData.text || ''
          },
          prompts: selectedPrompts
        }
      })

      if (response.error) {
        console.error('Analysis error:', response.error)
        toast.error(`Analysis failed: ${response.error.message}`)
        return
      }

      const data = response.data
      console.log('Analysis result:', data)
      setResult(data)
      toast.success('Risk analysis completed successfully!')
      
    } catch (error) {
      console.error('Network error during analysis:', error)
      toast.error('Failed to connect to analysis service. Please try again.')
    } finally {
      setLoading(false)
    }
  }


  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Risk Analysis</h1>
        <p className="text-muted-foreground">
          Analyze uploaded financial documents using advanced risk assessment models
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Document Analysis</span>
            </CardTitle>
            <CardDescription>
              Select a document and analysis types for comprehensive risk assessment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Document Selection Section */}
            <div className="space-y-4">
              <Label>Select Document</Label>
              {availableDocuments.length > 0 ? (
                <Select value={selectedDocument} onValueChange={setSelectedDocument}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Choose a document to analyze" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableDocuments.map((doc) => (
                      <SelectItem key={doc.id} value={doc.id}>
                        <div className="flex items-center space-x-2">
                          <FileText className="h-4 w-4" />
                          <span>{doc.company_name || 'Unknown Company'} - {doc.document_id}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="flex items-center space-x-2 p-3 border rounded-lg bg-muted/50">
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    No documents available. Please upload a document first.
                  </span>
                </div>
              )}

              {/* Document Info */}
              {selectedDocument && availableDocuments.length > 0 && (
                <div className="p-3 border rounded-lg bg-muted/20">
                  <div className="text-sm">
                    <div className="font-medium">Selected Document:</div>
                    <div className="text-muted-foreground">
                      {availableDocuments.find(doc => doc.id === selectedDocument)?.company_name}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      ID: {selectedDocument}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Analysis Types Section */}
            <div className="space-y-4">
              <Label>Analysis Types</Label>
              <div className="grid grid-cols-1 gap-3">
                {AVAILABLE_PROMPTS.map((prompt) => (
                  <div key={prompt.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                    <Checkbox
                      id={prompt.id}
                      checked={selectedPrompts.includes(prompt.id)}
                      onCheckedChange={() => togglePrompt(prompt.id)}
                      className="mt-1"
                    />
                    <div className="grid gap-1.5 leading-none">
                      <label
                        htmlFor={prompt.id}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                      >
                        {prompt.name}
                      </label>
                      <p className="text-xs text-muted-foreground">
                        {prompt.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Button 
              onClick={handleAnalysis} 
              disabled={loading || selectedPrompts.length === 0 || !selectedDocument}
              className="w-full"
            >
              {loading ? 'Analyzing...' : 'Run Risk Analysis'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
            <CardDescription>
              Risk analysis output from selected assessment models
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {result.results && result.results.length > 0 ? (
                  result.results.map((item: any, index: number) => {
                    const promptInfo = AVAILABLE_PROMPTS.find(p => p.id === item.prompt)
                    return (
                      <div key={index} className="border rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">
                            {promptInfo?.name || item.prompt}
                          </h4>
                          {item.analysis?.confidence && (
                            <div className="text-sm text-muted-foreground">
                              Confidence: {Math.round(item.analysis.confidence * 100)}%
                            </div>
                          )}
                        </div>
                        
                        {item.analysis?.risk_type && (
                          <div>
                            <span className="text-sm font-medium">Risk Type: </span>
                            <span className="text-sm text-muted-foreground">
                              {item.analysis.risk_type}
                            </span>
                          </div>
                        )}
                        
                        {item.analysis?.severity && (
                          <div>
                            <span className="text-sm font-medium">Severity: </span>
                            <span className="text-sm text-muted-foreground">
                              {item.analysis.severity}/10
                            </span>
                          </div>
                        )}
                        
                        {item.analysis?.summary && (
                          <p className="text-sm text-muted-foreground">
                            {item.analysis.summary}
                          </p>
                        )}
                        
                        {item.analysis?.key_findings && (
                          <div>
                            <div className="text-sm font-medium mb-2">Key Findings:</div>
                            <ul className="text-xs text-muted-foreground space-y-1">
                              {item.analysis.key_findings.map((finding: string, idx: number) => (
                                <li key={idx} className="flex items-start space-x-2">
                                  <span className="w-1 h-1 bg-current rounded-full mt-2 flex-shrink-0" />
                                  <span>{finding}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {item.analysis?.recommendations && (
                          <div>
                            <div className="text-sm font-medium mb-2">Recommendations:</div>
                            <ul className="text-xs text-muted-foreground space-y-1">
                              {item.analysis.recommendations.map((rec: string, idx: number) => (
                                <li key={idx} className="flex items-start space-x-2">
                                  <span className="w-1 h-1 bg-current rounded-full mt-2 flex-shrink-0" />
                                  <span>{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )
                  })
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    <p>No analysis results available</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a document and analysis types to see results here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Risk Visualization Section */}
      {result && (
        <RiskVisualization 
          analysisData={result} 
          companyName={result.company_name || "Unknown Company"}
        />
      )}
    </div>
  )
}

export default RiskAnalysis