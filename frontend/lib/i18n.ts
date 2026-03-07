export type Locale = "en" | "ko";

const translations = {
  en: {
    nav: {
      create: "Create",
      howToApply: "How to Apply",
    },
    footer: {
      openSource: "Open source project. Not affiliated with Tesla, Inc.",
      viewSource: "View source on GitHub",
    },
    home: {
      heroTitle: "Turn Your Kid's Drawing Into a Tesla Wrap 🖍️",
      heroSubtitle:
        "Print the template, let your child color it, snap a photo, and get a custom Tesla wrap in seconds!",
      steps: ["Print & Color 🖍️", "Upload Photo 📸", "Download PNG 🎉", "Apply to Tesla 🚗"],
      step1Header: "1. Select Your Tesla Model",
      step2Header: "2. Download & Print Template",
      step3Header: "3. Upload Your Masterpiece",
      downloadTemplate: (model: string) => `Download ${model} Template (PDF) ⬇️`,
      templateHint:
        "Print on A4 or Letter paper. Have your child color the template with crayons or markers!",
      startOver: "Start over with a new photo",
      tryAgain: "Try again",
      tipsTitle: "💡 Tips for best results",
      tips: [
        "Place the template on a flat surface in good lighting",
        "Make sure all 4 corner markers are visible in the photo",
        "Avoid shadows or reflections over the markers",
        "Take the photo straight on, not at an angle",
      ],
      unexpectedError: "Unexpected error. Please try again.",
    },
    guide: {
      title: "How to Apply Your Wrap",
      subtitle:
        "Tesla wraps are transferred via USB drive — no app or internet connection needed inside the car.",
      steps: [
        {
          title: "Prepare Your USB Drive",
          description:
            "Use a USB drive formatted as exFAT or FAT32 (MS-DOS FAT on Mac). NTFS is not supported by Tesla.",
          detailMac: "On Mac: Open Disk Utility → select your USB → Erase → Format: MS-DOS (FAT)",
          detailWindows:
            "On Windows: Right-click USB in Explorer → Format → File System: exFAT or FAT32",
        },
        {
          title: "Create the Wraps Folder",
          description: 'Create a folder named exactly "Wraps" at the root of the USB drive. The name is case-sensitive.',
          detail: "Your USB structure should look like: USB_DRIVE/Wraps/your-wrap.png",
        },
        {
          title: "Copy Your PNG File",
          description:
            "Move the downloaded PNG file into the Wraps folder. You can have up to 10 wrap images at a time.",
          detail:
            "Filenames must use only letters, numbers, underscores, dashes, and spaces (max 30 characters). The downloaded file is already named correctly.",
        },
        {
          title: "Insert USB into Your Tesla",
          description:
            "Plug the USB drive into any USB port in your Tesla. Wait a moment for it to be recognized.",
        },
        {
          title: "Open Paint Shop in Toybox",
          description: 'On your Tesla touchscreen: tap "Toybox" → "Paint Shop" → tap the "Wraps" tab.',
          detail:
            "Your custom wrap will appear in the list. Tap it to apply. The 3D car model will update in real time.",
        },
      ],
      importantTitle: "Important Notes",
      importantNotes: [
        "Do not store firmware or map update files on the same USB drive",
        "NTFS-formatted drives are not supported",
        "The wrap only affects the in-car 3D visualization — not the physical car",
        "Wraps persist until you remove them in Paint Shop",
      ],
      backLink: "← Back to Create a Wrap",
    },
    modelSelector: {
      sedan: "Sedan",
      suv: "SUV / Crossover",
    },
    uploader: {
      dropHere: "Drop your child's masterpiece here! 🎨",
      clickToBrowse: "or click to browse files 📁",
      fileTypes: "JPEG, PNG, WEBP, HEIC · max 20MB",
      ariaLabel: "Drop image here or click to upload",
      invalidType: "Please upload a JPEG, PNG, WEBP, or HEIC image.",
      tooLarge: "File is too large. Maximum size is 20MB.",
      takePhoto: "Snap a Photo! 📸",
    },
    status: {
      uploading: "Uploading image...",
      detecting: "Detecting alignment markers...",
      removing_bg: "Removing background...",
      compositing: "Applying to Tesla template...",
      previewing: "Preview ready!",
      done: "Your wrap is ready! 🎉",
      errorFallback: "Something went wrong. Please try again.",
    },
    download: {
      button: "Download Wrap PNG 🎉",
      guideLink: "How to apply it to your Tesla →",
    },
    preview: {
      title: "Your Tesla Wrap Preview 🎨",
      subtitle: "This is how your wrap will look. Happy with it?",
      download: "Download Wrap PNG 🎉",
      tryAgain: "Try Again",
      guideLink: "How to apply it to your Tesla →",
    },
  },
  ko: {
    nav: {
      create: "만들기",
      howToApply: "적용 방법",
    },
    footer: {
      openSource: "오픈 소스 프로젝트. Tesla, Inc.와 무관합니다.",
      viewSource: "GitHub에서 소스 보기",
    },
    home: {
      heroTitle: "아이의 그림을 테슬라 랩으로 만들어보세요 🖍️",
      heroSubtitle:
        "템플릿을 출력하고, 아이가 색칠하고, 사진을 찍으면 테슬라 커스텀 랩 파일이 뚝딱 완성!",
      steps: ["출력 & 색칠 🖍️", "사진 업로드 📸", "PNG 다운로드 🎉", "테슬라에 적용 🚗"],
      step1Header: "1. 테슬라 모델 선택",
      step2Header: "2. 템플릿 다운로드 & 출력",
      step3Header: "3. 작품 사진 업로드",
      downloadTemplate: (model: string) => `${model} 템플릿 다운로드 (PDF) ⬇️`,
      templateHint: "A4 또는 Letter 용지에 출력하세요. 아이가 크레용이나 마커로 신나게 색칠하도록 해주세요!",
      startOver: "새 사진으로 다시 시작",
      tryAgain: "다시 시도",
      tipsTitle: "💡 더 좋은 결과를 위한 팁",
      tips: [
        "템플릿을 평평한 곳에 놓고 밝은 조명에서 촬영하세요",
        "사진에 4개의 모서리 마커가 모두 보이는지 확인하세요",
        "마커 위에 그림자나 반사광이 없도록 하세요",
        "기울이지 말고 정면에서 찍어주세요",
      ],
      unexpectedError: "예기치 못한 오류가 발생했습니다. 다시 시도해 주세요.",
    },
    guide: {
      title: "랩 적용 방법",
      subtitle: "테슬라 랩은 USB 드라이브로 전송합니다. 차 안에서 앱이나 인터넷 연결이 필요 없습니다.",
      steps: [
        {
          title: "USB 드라이브 준비",
          description:
            "exFAT 또는 FAT32(Mac에서는 MS-DOS FAT)로 포맷된 USB를 사용하세요. NTFS는 테슬라에서 지원하지 않습니다.",
          detailMac:
            "Mac: 디스크 유틸리티 열기 → USB 선택 → 지우기 → 포맷: MS-DOS (FAT)",
          detailWindows:
            "Windows: 탐색기에서 USB 우클릭 → 포맷 → 파일 시스템: exFAT 또는 FAT32",
        },
        {
          title: "Wraps 폴더 생성",
          description: 'USB 루트에 정확히 "Wraps"라는 이름의 폴더를 만드세요. 이름은 대소문자를 구분합니다.',
          detail: "USB 구조: USB_DRIVE/Wraps/your-wrap.png",
        },
        {
          title: "PNG 파일 복사",
          description:
            "다운로드한 PNG 파일을 Wraps 폴더에 넣으세요. 최대 10개의 랩 이미지를 저장할 수 있습니다.",
          detail:
            "파일명은 영문자, 숫자, 언더스코어, 대시, 공백만 사용 가능하며 최대 30자입니다. 다운로드된 파일은 이미 올바른 이름으로 저장됩니다.",
        },
        {
          title: "테슬라에 USB 연결",
          description: "USB 드라이브를 테슬라의 USB 포트에 꽂으세요. 인식될 때까지 잠시 기다리세요.",
        },
        {
          title: "Toybox에서 Paint Shop 열기",
          description: '테슬라 터치스크린: "Toybox" → "Paint Shop" → "Wraps" 탭 선택',
          detail: "목록에서 커스텀 랩을 선택하여 적용하세요. 3D 차량 모델이 실시간으로 업데이트됩니다.",
        },
      ],
      importantTitle: "주의 사항",
      importantNotes: [
        "같은 USB에 펌웨어나 지도 업데이트 파일을 함께 저장하지 마세요",
        "NTFS 포맷 드라이브는 지원되지 않습니다",
        "랩은 차량 내 3D 시각화에만 적용됩니다. 실제 차량 외관은 변경되지 않습니다",
        "Paint Shop에서 제거하기 전까지 랩이 유지됩니다",
      ],
      backLink: "← 랩 만들기로 돌아가기",
    },
    modelSelector: {
      sedan: "세단",
      suv: "SUV / 크로스오버",
    },
    uploader: {
      dropHere: "우리 아이의 멋진 작품을 이곳에 쏙 넣어주세요! 🎨",
      clickToBrowse: "또는 클릭해서 파일을 골라주세요 📁",
      fileTypes: "JPEG, PNG, WEBP, HEIC · 최대 20MB",
      ariaLabel: "이미지를 드래그하거나 클릭하여 업로드",
      invalidType: "JPEG, PNG, WEBP 또는 HEIC 이미지를 업로드해 주세요.",
      tooLarge: "파일이 너무 큽니다. 최대 크기는 20MB입니다.",
      takePhoto: "찰칵! 작품 사진 찍기 📸",
    },
    status: {
      uploading: "이미지 업로드 중...",
      detecting: "마커 감지 중...",
      removing_bg: "배경 제거 중...",
      compositing: "테슬라 템플릿에 적용 중...",
      previewing: "미리보기 준비 완료!",
      done: "랩이 완성되었습니다! 🎉",
      errorFallback: "오류가 발생했습니다. 다시 시도해 주세요.",
    },
    download: {
      button: "랩 PNG 다운로드 🎉",
      guideLink: "테슬라에 적용하는 방법 →",
    },
    preview: {
      title: "테슬라 랩 미리보기 🎨",
      subtitle: "완성된 랩입니다. 마음에 드시나요?",
      download: "랩 PNG 다운로드 🎉",
      tryAgain: "다시 시도",
      guideLink: "테슬라에 적용하는 방법 →",
    },
  },
} as const;

export type T = typeof translations.en;

export function getT(locale: Locale): T {
  return translations[locale] as unknown as T;
}
