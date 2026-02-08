import Document, { Html, Head, Main, NextScript } from "next/document";

export default class MyDocument extends Document {
  render() {
    const title = "ISMS-Bunny";
    const description = "MSP-friendly ISMS and trust center scaffold";
    const image = "/logo-1024.png"; // in public/
    const themeColor = "#4B2C82";

    return (
      <Html lang="en">
        <Head>
          <link rel="icon" href="/favicon.ico" />
          <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
          <link rel="icon" type="image/png" sizes="512x512" href="/logo-512.png" />
          <link rel="icon" type="image/png" sizes="256x256" href="/logo-256.png" />
          <meta name="theme-color" content={themeColor} />
          <meta name="description" content={description} />

          {/* Open Graph */}
          <meta property="og:type" content="website" />
          <meta property="og:title" content={title} />
          <meta property="og:description" content={description} />
          <meta property="og:image" content={image} />
          <meta property="og:url" content="https://github.com/guiltykeyboard/isms-bunny" />

          {/* Twitter */}
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content={title} />
          <meta name="twitter:description" content={description} />
          <meta name="twitter:image" content={image} />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}
