"use client";

import { useEffect } from "react";
import { SplitPaneCanvas } from "@/components/SplitPaneCanvas";
import { useNOCStore } from "@/store/useNOCStore";

export default function Home() {
  const initDashboard = useNOCStore((state) => state.initDashboard);

  useEffect(() => {
    // Initialize dashboard by querying real backend health & audit history
    initDashboard();
  }, [initDashboard]);

  return <SplitPaneCanvas />;
}
