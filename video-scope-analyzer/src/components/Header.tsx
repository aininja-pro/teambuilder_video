import Image from 'next/image'
import Link from 'next/link'

interface HeaderProps {
  onProjectsClick?: () => void
  onAnalyzeVideoClick?: () => void
}

export default function Header({ onProjectsClick, onAnalyzeVideoClick }: HeaderProps) {
  return (
    <header className="bg-black border-b border-gray-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-24">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <img
                src="/assets/team-builders-logo.png"
                alt="Team Builders Logo"
                width={200}
                height={32}
              />
            </Link>
          </div>

          {/* Centered Title - Hidden on mobile to prevent overlap with logo */}
          <div className="hidden md:block absolute left-1/2 transform -translate-x-1/2">
            <h1 className="text-xl font-bold text-white">Video Scope Analyzer</h1>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <button 
              onClick={onAnalyzeVideoClick}
              className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Analyze Video
            </button>
            <button 
              onClick={onProjectsClick}
              className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Projects
            </button>
          </nav>

          {/* Mobile menu button (future use) */}
          <div className="md:hidden">
            <button className="text-gray-300 hover:text-white p-2">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}