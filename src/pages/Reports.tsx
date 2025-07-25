import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import { FileText, Download, Calendar, TrendingUp, BarChart3 } from 'lucide-react'

interface Report {
  id: string
  title: string
  type: string
  date: string
  status: string
}

const Reports = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [reports, setReports] = useState<Report[]>([
    {
      id: 'rpt_001',
      title: 'Q4 2024 Risk Assessment',
      type: 'Risk Analysis',
      date: '2024-12-15',
      status: 'Completed'
    },
    {
      id: 'rpt_002', 
      title: 'Compliance Review Report',
      type: 'Compliance',
      date: '2024-12-10',
      status: 'Completed'
    },
    {
      id: 'rpt_003',
      title: 'Market Risk Analysis',
      type: 'Market Analysis',
      date: '2024-12-05',
      status: 'Completed'
    }
  ])

  const generateReport = async () => {
    setLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/generate-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id || 'demo-user',
          report_type: 'comprehensive_risk_analysis',
          include_recommendations: true
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const newReport: Report = {
          id: `rpt_${Date.now()}`,
          title: `Generated Report - ${new Date().toLocaleDateString()}`,
          type: 'Comprehensive Analysis',
          date: new Date().toISOString().split('T')[0],
          status: 'Completed'
        }
        setReports(prev => [newReport, ...prev])
        toast.success('Report generated successfully!')
      } else {
        // Mock report generation
        const newReport: Report = {
          id: `rpt_${Date.now()}`,
          title: `Demo Report - ${new Date().toLocaleDateString()}`,
          type: 'Risk Analysis',
          date: new Date().toISOString().split('T')[0],
          status: 'Completed'
        }
        setReports(prev => [newReport, ...prev])
        toast.success('Demo report generated (API unavailable)')
      }
    } catch (error) {
      // Mock report generation
      const newReport: Report = {
        id: `rpt_${Date.now()}`,
        title: `Demo Report - ${new Date().toLocaleDateString()}`,
        type: 'Risk Analysis',
        date: new Date().toISOString().split('T')[0],
        status: 'Completed'
      }
      setReports(prev => [newReport, ...prev])
      toast.success('Demo report generated (API unavailable)')
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = (reportId: string, title: string) => {
    // Mock download functionality
    toast.success(`Downloading ${title}...`)
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Reports</h1>
          <p className="text-muted-foreground">
            Generate and manage your financial risk reports
          </p>
        </div>
        <Button onClick={generateReport} disabled={loading}>
          {loading ? 'Generating...' : 'Generate Report'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reports.length}</div>
            <p className="text-xs text-muted-foreground">
              Generated this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Latest Report</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {reports[0]?.date ? new Date(reports[0].date).toLocaleDateString() : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Most recent generation
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Report Types</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(reports.map(r => r.type)).size}
            </div>
            <p className="text-xs text-muted-foreground">
              Different categories
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Report History</CardTitle>
          <CardDescription>
            View and download your generated reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length > 0 ? (
            <div className="space-y-4">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 border border-border rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <FileText className="h-8 w-8 text-primary" />
                    <div>
                      <h3 className="font-medium text-foreground">{report.title}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>Type: {report.type}</span>
                        <span>•</span>
                        <span>Date: {new Date(report.date).toLocaleDateString()}</span>
                        <span>•</span>
                        <span className="text-green-600">Status: {report.status}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadReport(report.id, report.title)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No reports generated yet</p>
              <p className="text-sm text-muted-foreground">Click "Generate Report" to create your first report</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Report Templates</CardTitle>
          <CardDescription>
            Available report types and formats
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                title: 'Risk Assessment Report',
                description: 'Comprehensive risk analysis with recommendations',
                icon: TrendingUp
              },
              {
                title: 'Compliance Report', 
                description: 'Regulatory compliance status and requirements',
                icon: FileText
              },
              {
                title: 'Market Analysis Report',
                description: 'Market risk factors and exposure analysis',
                icon: BarChart3 
              },
              {
                title: 'Financial Summary',
                description: 'High-level financial health overview',
                icon: TrendingUp
              },
              {
                title: 'Audit Report',
                description: 'Detailed audit findings and recommendations',
                icon: FileText
              },
              {
                title: 'Executive Summary',
                description: 'Executive-level risk and performance summary',
                icon: BarChart3
              }
            ].map((template, index) => {
              const Icon = template.icon
              return (
                <div
                  key={index}
                  className="p-4 border border-border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                >
                  <Icon className="h-8 w-8 text-primary mb-2" />
                  <h3 className="font-medium text-foreground mb-1">{template.title}</h3>
                  <p className="text-sm text-muted-foreground">{template.description}</p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Reports