import { ShowcasePage } from "@/components/ShowcasePage";
import { loadShowcaseData } from "@/lib/data";

export default function ReimaginingAlbertaEdFlowIntelligence() {
  const data = loadShowcaseData();
  return <ShowcasePage data={data} />;
}
