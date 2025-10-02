import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SJTU 体育跑步上传工具',
  description: '上海交通大学体育跑步数据上传工具 - Web版本',
  keywords: ['SJTU', '上海交通大学', '体育', '跑步', '上传工具'],
  authors: [{ name: 'SJTU Running Tool' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">
        <div className="min-h-screen">
          {children}
        </div>
      </body>
    </html>
  )
}
