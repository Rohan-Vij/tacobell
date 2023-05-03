import { ReactNode } from "react";

type FullscreenProps = {
    children: ReactNode;
}

const Fullscreen: React.FC<FullscreenProps> = ({ children }) => {
  return (
    <div className="h-screen">
        {children}
    </div>
  )
}

export default Fullscreen;