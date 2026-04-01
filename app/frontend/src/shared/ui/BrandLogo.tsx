import verbaLogoSrc from "../assets/verba-logo.png";
import { cn } from "../utils/cn";

type BrandLogoProps = {
  alt?: string;
  className?: string;
  imageClassName?: string;
};

export function BrandLogo({
  alt = "Verba",
  className,
  imageClassName,
}: BrandLogoProps) {
  return (
    <div className={cn("inline-flex shrink-0 items-center", className)}>
      <img
        src={verbaLogoSrc}
        alt={alt}
        draggable={false}
        decoding="async"
        className={cn("block h-auto w-full object-contain", imageClassName)}
      />
    </div>
  );
}
