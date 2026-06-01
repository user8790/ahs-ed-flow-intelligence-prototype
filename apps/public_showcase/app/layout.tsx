import "./styles.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Reimagining Alberta ED Flow Intelligence",
  description: "Public-safe ED flow intelligence showcase using open-data-shaped and synthetic artifacts only."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
