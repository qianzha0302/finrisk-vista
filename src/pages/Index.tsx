import { useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'
import { BarChart3, Shield, TrendingUp, FileText, Users, Zap, Upload, Search } from 'lucide-react'

const Index = () => {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  // If user is authenticated, show the dashboard content instead of landing page
  if (user) {
    const features = [
      {
        icon: Upload,
        title: 'Document Upload',
        description: 'Upload financial documents for comprehensive risk analysis',
        href: '/upload'
      },
      {
        icon: BarChart3,
        title: 'Risk Analysis',
        description: 'AI-powered risk assessment and categorization',
        href: '/analysis'
      },
      {
        icon: Search,
        title: 'Smart Query',
        description: 'Ask questions about your financial documents',
        href: '/query'
      },
      {
        icon: FileText,
        title: 'Reports',
        description: 'Generate detailed risk assessment reports',
        href: '/reports'
      }
    ]

    return (
      <div className="space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-foreground">
            Financial Risk Analyzer
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Advanced AI-powered platform for comprehensive financial document analysis and risk assessment
          </p>
          <p className="text-sm text-muted-foreground">
            Welcome back, {user.email}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Card key={feature.title} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Icon className="h-6 w-6 text-primary" />
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="mb-4">
                    {feature.description}
                  </CardDescription>
                  <Link to={feature.href}>
                    <Button variant="outline" size="sm" className="w-full">
                      Get Started
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-12">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5" />
                <span>Key Benefits</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start space-x-2">
                  <Shield className="h-4 w-4 text-green-500 mt-1" />
                  <span className="text-sm">Comprehensive risk identification and assessment</span>
                </li>
                <li className="flex items-start space-x-2">
                  <Shield className="h-4 w-4 text-green-500 mt-1" />
                  <span className="text-sm">Advanced AI-powered document analysis</span>
                </li>
                <li className="flex items-start space-x-2">
                  <Shield className="h-4 w-4 text-green-500 mt-1" />
                  <span className="text-sm">Real-time insights and recommendations</span>
                </li>
                <li className="flex items-start space-x-2">
                  <Shield className="h-4 w-4 text-green-500 mt-1" />
                  <span className="text-sm">Secure document processing and storage</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Start</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                    1
                  </div>
                  <span className="text-sm">Upload your financial documents</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                    2
                  </div>
                  <span className="text-sm">Select analysis types</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                    3
                  </div>
                  <span className="text-sm">Review AI-generated risk insights</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Landing page for non-authenticated users

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold text-foreground">FinRiskGPT</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/auth">
                <Button variant="outline">
                  Login
                </Button>
              </Link>
              <Link to="/auth">
                <Button>
                  Sign Up
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            AI-Powered Financial 
            <span className="text-primary block">Risk Analysis</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Transform your financial risk management with advanced AI analysis. 
            Upload documents, get insights, and make data-driven decisions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/auth">
              <Button size="lg" className="px-8">
                Get Started Free
              </Button>
            </Link>
            <Link to="/auth">
              <Button size="lg" variant="outline">
                View Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Powerful Risk Analysis Features
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Everything you need to analyze, understand, and manage financial risks
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <Shield className="h-12 w-12 text-primary mb-4" />
                <CardTitle>Risk Assessment</CardTitle>
                <CardDescription>
                  AI-powered analysis of financial documents to identify and quantify risks
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <FileText className="h-12 w-12 text-primary mb-4" />
                <CardTitle>Document Analysis</CardTitle>
                <CardDescription>
                  Upload and analyze financial statements, reports, and compliance documents
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <TrendingUp className="h-12 w-12 text-primary mb-4" />
                <CardTitle>Trend Analysis</CardTitle>
                <CardDescription>
                  Identify patterns and trends in financial data for better decision making
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <Zap className="h-12 w-12 text-primary mb-4" />
                <CardTitle>Real-time Insights</CardTitle>
                <CardDescription>
                  Get instant analysis and recommendations based on your financial data
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <BarChart3 className="h-12 w-12 text-primary mb-4" />
                <CardTitle>Interactive Reports</CardTitle>
                <CardDescription>
                  Generate comprehensive reports with visualizations and actionable insights
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <Users className="h-12 w-12 text-primary mb-4" />
                <CardTitle>Team Collaboration</CardTitle>
                <CardDescription>
                  Share insights and collaborate with your team on risk management strategies
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Ready to Transform Your Risk Management?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join thousands of financial professionals using FinRiskGPT for smarter risk analysis
          </p>
          <Link to="/auth">
            <Button size="lg" className="px-8">
              Start Your Free Trial
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-6 w-6 text-primary" />
              <span className="font-bold text-foreground">FinRiskGPT</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2024 FinRiskGPT. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Index;
