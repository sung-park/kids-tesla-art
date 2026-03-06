import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How to Apply Your Wrap | Kids Tesla Art",
  description:
    "Step-by-step guide to transfer your custom wrap to your Tesla via USB drive.",
};

const steps = [
  {
    number: 1,
    title: "Prepare Your USB Drive",
    description:
      "Use a USB drive formatted as exFAT or FAT32 (MS-DOS FAT on Mac). NTFS is not supported by Tesla.",
    detail: (
      <>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          <strong>On Mac:</strong> Open Disk Utility → select your USB → Erase → Format: MS-DOS (FAT)
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          <strong>On Windows:</strong> Right-click USB in Explorer → Format → File System: exFAT or FAT32
        </p>
      </>
    ),
  },
  {
    number: 2,
    title: "Create the Wraps Folder",
    description: (
      <>
        Create a folder named exactly{" "}
        <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded font-mono text-sm">
          Wraps
        </code>{" "}
        at the root of the USB drive. The name is case-sensitive.
      </>
    ),
    detail: (
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
        Your USB structure should look like:{" "}
        <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded font-mono text-sm">
          USB_DRIVE/Wraps/your-wrap.png
        </code>
      </p>
    ),
  },
  {
    number: 3,
    title: "Copy Your PNG File",
    description:
      "Move the downloaded PNG file into the Wraps folder. You can have up to 10 wrap images at a time.",
    detail: (
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
        Filenames must use only letters, numbers, underscores, dashes, and spaces (max 30 characters). The downloaded file is already named correctly.
      </p>
    ),
  },
  {
    number: 4,
    title: "Insert USB into Your Tesla",
    description:
      "Plug the USB drive into any USB port in your Tesla. Wait a moment for it to be recognized.",
    detail: null,
  },
  {
    number: 5,
    title: "Open Paint Shop in Toybox",
    description: (
      <>
        On your Tesla touchscreen: tap{" "}
        <strong>Toybox</strong> → <strong>Paint Shop</strong> → tap the{" "}
        <strong>Wraps</strong> tab.
      </>
    ),
    detail: (
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
        Your custom wrap will appear in the list. Tap it to apply. The 3D car model will update in real time.
      </p>
    ),
  },
];

export default function GuidePage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-tesla-dark dark:text-white mb-3">
          How to Apply Your Wrap
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Tesla wraps are transferred via USB drive — no app or internet connection needed inside the car.
        </p>
      </div>

      <div className="space-y-6">
        {steps.map((step) => (
          <div
            key={step.number}
            className="flex gap-4 p-5 rounded-xl bg-gray-50 dark:bg-gray-800"
          >
            <div className="shrink-0 w-8 h-8 rounded-full bg-tesla-red text-white text-sm font-bold flex items-center justify-center">
              {step.number}
            </div>
            <div className="min-w-0">
              <h2 className="font-semibold text-tesla-dark dark:text-white">
                {step.title}
              </h2>
              <p className="text-gray-700 dark:text-gray-300 text-sm mt-1">
                {step.description}
              </p>
              {step.detail}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 p-5 rounded-xl border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950">
        <h3 className="font-semibold text-amber-800 dark:text-amber-300 mb-2">
          Important Notes
        </h3>
        <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-1.5 list-disc list-inside">
          <li>Do not store firmware or map update files on the same USB drive</li>
          <li>NTFS-formatted drives are not supported</li>
          <li>The wrap only affects the in-car 3D visualization — not the physical car</li>
          <li>Wraps persist until you remove them in Paint Shop</li>
        </ul>
      </div>

      <div className="mt-8 text-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-tesla-red hover:underline"
        >
          ← Back to Create a Wrap
        </Link>
      </div>
    </div>
  );
}
