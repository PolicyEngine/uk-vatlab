import type { Metadata } from 'next'
import { Roboto_Serif, Roboto_Mono } from 'next/font/google'
import Script from 'next/script'
import './globals.css'

const GA_ID = 'G-2YHG89FY0N'
const TOOL_NAME = 'uk-vatlab'

const robotoSerif = Roboto_Serif({ 
  weight: ['300', '400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-roboto-serif'
})

const robotoMono = Roboto_Mono({ 
  weight: ['300', '400', '500'],
  subsets: ['latin'],
  variable: '--font-roboto-mono'
})

export const metadata: Metadata = {
  title: 'VAT policy simulator',
  description: 'Analyse the impact of VAT registration threshold reforms',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${robotoSerif.variable} ${robotoMono.variable}`}>
      <body className="font-sans">
        {children}
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="gtag-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}', { tool_name: '${TOOL_NAME}' });
          `}
        </Script>
        <Script id="engagement-tracking" strategy="afterInteractive">
          {`
            (function() {
              var TOOL_NAME = '${TOOL_NAME}';
              if (typeof window === 'undefined' || !window.gtag) return;

              var scrollFired = {};
              window.addEventListener('scroll', function() {
                var docHeight = document.documentElement.scrollHeight - window.innerHeight;
                if (docHeight <= 0) return;
                var pct = Math.floor((window.scrollY / docHeight) * 100);
                [25, 50, 75, 100].forEach(function(m) {
                  if (pct >= m && !scrollFired[m]) {
                    scrollFired[m] = true;
                    window.gtag('event', 'scroll_depth', { percent: m, tool_name: TOOL_NAME });
                  }
                });
              }, { passive: true });

              [30, 60, 120, 300].forEach(function(sec) {
                setTimeout(function() {
                  if (document.visibilityState !== 'hidden') {
                    window.gtag('event', 'time_on_tool', { seconds: sec, tool_name: TOOL_NAME });
                  }
                }, sec * 1000);
              });

              document.addEventListener('click', function(e) {
                var link = e.target && e.target.closest ? e.target.closest('a') : null;
                if (!link || !link.href) return;
                try {
                  var url = new URL(link.href, window.location.origin);
                  if (url.hostname && url.hostname !== window.location.hostname) {
                    window.gtag('event', 'outbound_click', {
                      url: link.href,
                      target_hostname: url.hostname,
                      tool_name: TOOL_NAME
                    });
                  }
                } catch (err) {}
              });
            })();
          `}
        </Script>
      </body>
    </html>
  )
}