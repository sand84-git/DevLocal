import { useAppStore } from "./store/useAppStore";
import Header from "./components/Header";
import DataSourceScreen from "./screens/DataSourceScreen";
import LoadingScreen from "./screens/LoadingScreen";
import KoReviewScreen from "./screens/KoReviewScreen";
import TranslatingScreen from "./screens/TranslatingScreen";
import FinalReviewScreen from "./screens/FinalReviewScreen";
import DoneScreen from "./screens/DoneScreen";

function CurrentScreen() {
  const currentStep = useAppStore((s) => s.currentStep);

  switch (currentStep) {
    case "idle":
      return <DataSourceScreen />;
    case "loading":
      return <LoadingScreen />;
    case "ko_review":
      return <KoReviewScreen />;
    case "translating":
      return <TranslatingScreen />;
    case "final_review":
      return <FinalReviewScreen />;
    case "done":
      return <DoneScreen />;
    default:
      return <DataSourceScreen />;
  }
}

export default function App() {
  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-bg-page font-display text-text-main antialiased">
      <Header />
      <CurrentScreen />
    </div>
  );
}
