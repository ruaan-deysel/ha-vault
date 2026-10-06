import {
  mdiAlertCircle,
  mdiAlertOutline,
  mdiArrowRight,
  mdiBriefcaseOutline,
  mdiCheck,
  mdiCheckCircle,
  mdiChevronDown,
  mdiChevronUp,
  mdiClockOutline,
  mdiClose,
  mdiCloseCircle,
  mdiCog,
  mdiDatabase,
  mdiFileDocumentOutline,
  mdiFolder,
  mdiFolderNetwork,
  mdiFormatListBulleted,
  mdiHarddisk,
  mdiHeart,
  mdiHeartOutline,
  mdiHistory,
  mdiInformation,
  mdiLock,
  mdiLockOpenVariant,
  mdiPackageVariantClosed,
  mdiPlay,
  mdiProgressClock,
  mdiRestart,
  mdiServer,
  mdiShieldAlert,
  mdiShieldCheck,
  mdiShieldOutline,
  mdiSpeedometer,
  mdiSync,
  mdiTagOutline,
} from "@mdi/js";
import { html, type TemplateResult } from "lit";

export {
  mdiAlertCircle,
  mdiAlertOutline,
  mdiArrowRight,
  mdiBriefcaseOutline,
  mdiCheck,
  mdiCheckCircle,
  mdiChevronDown,
  mdiChevronUp,
  mdiClockOutline,
  mdiClose,
  mdiCloseCircle,
  mdiCog,
  mdiDatabase,
  mdiFileDocumentOutline,
  mdiFolder,
  mdiFolderNetwork,
  mdiFormatListBulleted,
  mdiHarddisk,
  mdiHeart,
  mdiHeartOutline,
  mdiHistory,
  mdiInformation,
  mdiLock,
  mdiLockOpenVariant,
  mdiPackageVariantClosed,
  mdiPlay,
  mdiProgressClock,
  mdiRestart,
  mdiServer,
  mdiShieldAlert,
  mdiShieldCheck,
  mdiShieldOutline,
  mdiSpeedometer,
  mdiSync,
  mdiTagOutline,
};

export function iconTemplate(
  path: string,
  size = 20,
  className = "icon"
): TemplateResult {
  return html`
    <svg
      class="${className}"
      style="width: ${size}px; height: ${size}px;"
      viewBox="0 0 24 24"
    >
      <path d="${path}" fill="currentColor"></path>
    </svg>
  `;
}
