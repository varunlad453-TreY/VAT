"use client";

import { useEffect } from "react";
import { SplitPaneCanvas } from "@/components/SplitPaneCanvas";
import { useNOCStore } from "@/store/useNOCStore";

export default function Home() {
  const loadInitialSampleData = useNOCStore((state) => state.loadInitialSampleData);

  useEffect(() => {
    loadInitialSampleData();
  }, [loadInitialSampleData]);

  return <SplitPaneCanvas />;
}
