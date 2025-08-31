import Image from 'next/image'
import Link from 'next/link'

export default function Header() {
  return (
    <header className="bg-black border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-4">
              <Image
                src="/assets/team-builders-logo.png"
                alt="Team Builders Logo"
                width={48}
                height={48}
                className="h-12 w-12"
                priority
                quality={100}
              />
              <div className="text-white">
                <h1 className="text-xl font-bold">Video Scope Analyzer</h1>
              </div>
            </Link>
          </div>

          {/* Navigation (future use) */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link 
              href="/" 
              className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Analyze Video
            </Link>
            <Link 
              href="/projects" 
              className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Projects
            </Link>
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