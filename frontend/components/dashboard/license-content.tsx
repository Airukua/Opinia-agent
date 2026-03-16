"use client"

import * as React from "react"

import { Button } from "@/components/ui/button"

const licenseMeta = {
  name: "Custom License - Abdul Wahid Rukua",
  version: "1.0",
  effectiveDateISO: "2026-03-10",
  copyright: "Copyright (c) 2026 Abdul Wahid Rukua",
}

const content = {
  en: {
    section: "License Overview",
    versionLabel: "Version",
    effectiveLabel: "Effective",
    allRights: "All rights reserved, except as expressly granted below.",
    definitions: {
      title: "1. Definitions",
      items: [
        {
          term: "Software",
          text: "means this project, including source code, documentation, and related files.",
        },
        {
          term: "Personal Use",
          text: "means use by an individual for learning, research, hobby, or other non-commercial purposes.",
        },
        {
          term: "Commercial Use",
          text: "means any use intended for, directed toward, or resulting in revenue, profit, paid service, paid product, or business advantage.",
        },
        {
          term: "Net Profit",
          text: "means gross revenue directly attributable to the Software minus direct operational costs reasonably and consistently applied.",
        },
      ],
    },
    grant: {
      title: "2. Grant of Rights",
      items: [
        "Use the Software for Personal Use.",
        "Copy, modify, and share the Software for non-commercial purposes.",
        "Redistribute original or modified versions, provided this license is included.",
      ],
    },
    commercial: {
      title: "3. Commercial Use Condition",
      lead: "Commercial Use is permitted only if you agree to share at least two percent (2%) of Net Profit derived from the Software with the Licensor.",
      items: [
        "Provide periodic profit reporting upon reasonable request.",
        "Arrange payment of the 2% revenue share in good faith with the Licensor.",
        "Keep this license text in all substantial portions of the Software.",
      ],
    },
    attribution: {
      title: "4. Attribution",
      items: [
        "Retain the copyright notice.",
        "Retain this license text.",
        "Provide credit to Abdul Wahid Rukua.",
      ],
    },
    restrictions: {
      title: "5. Restrictions",
      items: [
        "Do not remove or misrepresent ownership and authorship.",
        "Do not claim this Software as exclusively your own original work without attribution.",
        "Do not use the Software in violation of applicable laws.",
      ],
    },
    warranty: {
      title: "6. Warranty Disclaimer",
      text: "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.",
    },
    liability: {
      title: "7. Limitation of Liability",
      text: "IN NO EVENT SHALL THE LICENSOR BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM OR IN CONNECTION WITH THE SOFTWARE OR ITS USE.",
    },
    termination: {
      title: "8. Termination",
      text: "Any violation of this license automatically terminates the rights granted herein. Rights may be reinstated only with explicit written permission from the Licensor.",
    },
    contact: {
      title: "Contact",
      lead: "For commercial arrangements and profit-sharing settlement, contact the Licensor:",
      name: "Abdul Wahid Rukua",
      email: "rukuaabdulwahid@gmail.com",
    },
    summary: {
      title: "Summary",
      items: [
        "Personal, non-commercial use is permitted.",
        "Commercial use requires a 2% net profit share.",
        "Attribution and license text must be retained.",
      ],
    },
    translateCta: "Terjemahkan ke Bahasa Indonesia",
    translateBack: "Translate to English",
  },
  id: {
    section: "Ringkasan Lisensi",
    versionLabel: "Versi",
    effectiveLabel: "Berlaku",
    allRights: "Hak cipta dilindungi, kecuali yang secara tegas diberikan di bawah ini.",
    definitions: {
      title: "1. Definisi",
      items: [
        {
          term: "Software",
          text: "adalah proyek ini, termasuk source code, dokumentasi, dan file terkait.",
        },
        {
          term: "Penggunaan Pribadi",
          text: "adalah penggunaan oleh individu untuk belajar, riset, hobi, atau tujuan non-komersial lainnya.",
        },
        {
          term: "Penggunaan Komersial",
          text: "adalah penggunaan yang ditujukan untuk atau menghasilkan pendapatan, profit, layanan berbayar, produk berbayar, atau keuntungan bisnis.",
        },
        {
          term: "Laba Bersih",
          text: "adalah pendapatan kotor yang berasal langsung dari Software dikurangi biaya operasional langsung yang wajar dan konsisten.",
        },
      ],
    },
    grant: {
      title: "2. Pemberian Hak",
      items: [
        "Menggunakan Software untuk Penggunaan Pribadi.",
        "Menyalin, memodifikasi, dan membagikan Software untuk tujuan non-komersial.",
        "Mendistribusikan ulang versi asli atau modifikasi dengan menyertakan lisensi ini.",
      ],
    },
    commercial: {
      title: "3. Syarat Penggunaan Komersial",
      lead: "Penggunaan komersial diperbolehkan hanya jika Anda setuju membagikan minimal dua persen (2%) dari Laba Bersih yang berasal dari Software kepada Pemberi Lisensi.",
      items: [
        "Memberikan laporan laba secara berkala jika diminta secara wajar.",
        "Mengatur pembayaran bagi hasil 2% dengan itikad baik kepada Pemberi Lisensi.",
        "Menyertakan teks lisensi ini pada semua bagian substansial Software.",
      ],
    },
    attribution: {
      title: "4. Atribusi",
      items: [
        "Mempertahankan pemberitahuan hak cipta.",
        "Mempertahankan teks lisensi ini.",
        "Memberikan kredit kepada Abdul Wahid Rukua.",
      ],
    },
    restrictions: {
      title: "5. Pembatasan",
      items: [
        "Tidak menghapus atau menyesatkan kepemilikan dan keaslian karya.",
        "Tidak mengklaim Software ini sebagai karya asli Anda secara eksklusif tanpa atribusi.",
        "Tidak menggunakan Software untuk tindakan yang melanggar hukum.",
      ],
    },
    warranty: {
      title: "6. Penafian Garansi",
      text: "SOFTWARE DIBERIKAN \"APA ADANYA\", TANPA JAMINAN APA PUN, BAIK TERSURAT MAUPUN TERSIRAT, TERMASUK NAMUN TIDAK TERBATAS PADA KELAYAKAN DIPERDAGANGKAN, KESESUAIAN UNTUK TUJUAN TERTENTU, DAN TIDAK MELANGGAR HAK PIHAK LAIN.",
    },
    liability: {
      title: "7. Batasan Tanggung Jawab",
      text: "DALAM KEADAAN APA PUN PEMBERI LISENSI TIDAK BERTANGGUNG JAWAB ATAS KLAIM, KERUSAKAN, ATAU TANGGUNG JAWAB LAIN, BAIK DALAM KONTRAK, PERBUATAN MELAWAN HUKUM, ATAU LAINNYA, YANG TIMBUL DARI ATAU BERKAITAN DENGAN SOFTWARE ATAU PENGGUNAANNYA.",
    },
    termination: {
      title: "8. Pengakhiran",
      text: "Pelanggaran atas lisensi ini secara otomatis mengakhiri hak yang diberikan. Hak dapat dipulihkan hanya dengan izin tertulis eksplisit dari Pemberi Lisensi.",
    },
    contact: {
      title: "Kontak",
      lead: "Untuk pengaturan komersial dan penyelesaian bagi hasil, hubungi Pemberi Lisensi:",
      name: "Abdul Wahid Rukua",
      email: "rukuaabdulwahid@gmail.com",
    },
    summary: {
      title: "Ringkasan",
      items: [
        "Penggunaan pribadi non-komersial diperbolehkan.",
        "Penggunaan komersial wajib bagi hasil 2% laba bersih.",
        "Atribusi dan teks lisensi harus dipertahankan.",
      ],
    },
    translateCta: "Terjemahkan ke Bahasa Indonesia",
    translateBack: "Translate to English",
  },
}

export function LicenseContent() {
  const [locale, setLocale] = React.useState<"en" | "id">("en")
  const t = content[locale]

  const formattedDate = new Intl.DateTimeFormat(locale === "id" ? "id-ID" : "en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(licenseMeta.effectiveDateISO))

  return (
    <div className="flex flex-col gap-6">
      <section className="rounded-xl border bg-background p-6">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex flex-col gap-2">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {t.section}
              </p>
              <h1 className="text-2xl font-semibold text-foreground">
                {licenseMeta.name}
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span>
                  {t.versionLabel} {licenseMeta.version}
                </span>
                <span className="h-1 w-1 rounded-full bg-muted-foreground/60" />
                <span>
                  {t.effectiveLabel} {formattedDate}
                </span>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={() => setLocale(locale === "en" ? "id" : "en")}
            >
              {locale === "en" ? t.translateCta : t.translateBack}
            </Button>
          </div>
          <div className="border-t pt-4 text-sm text-muted-foreground">
            <p>{licenseMeta.copyright}</p>
            <p>{t.allRights}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-xl border bg-background p-6">
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-lg font-semibold">{t.definitions.title}</h2>
              <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                {t.definitions.items.map((item) => (
                  <p key={item.term}>
                    <span className="font-medium text-foreground">{item.term}</span> {item.text}
                  </p>
                ))}
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.grant.title}</h2>
              <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
                {t.grant.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.commercial.title}</h2>
              <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                <p>{t.commercial.lead}</p>
                <ul className="space-y-2">
                  {t.commercial.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.attribution.title}</h2>
              <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
                {t.attribution.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.restrictions.title}</h2>
              <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
                {t.restrictions.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.warranty.title}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{t.warranty.text}</p>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.liability.title}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{t.liability.text}</p>
            </div>

            <div>
              <h2 className="text-lg font-semibold">{t.termination.title}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{t.termination.text}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <section className="rounded-xl border bg-background p-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              {t.contact.title}
            </h3>
            <p className="mt-3 text-sm text-muted-foreground">{t.contact.lead}</p>
            <p className="mt-3 text-base font-semibold text-foreground">{t.contact.name}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <a
                className="text-sm font-medium text-foreground underline-offset-4 hover:underline"
                href={`mailto:${t.contact.email}`}
              >
                {t.contact.email}
              </a>
              <Button asChild size="sm" className="h-8">
                <a href={`mailto:${t.contact.email}`}>Kirim Email</a>
              </Button>
            </div>
          </section>

          <section className="rounded-xl border bg-background p-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              {t.summary.title}
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {t.summary.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </div>
      </section>
    </div>
  )
}
