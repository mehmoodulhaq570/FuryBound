import type { Metadata } from "next";

import { TrainActivity } from "@/components/training/train-activity";

export const metadata: Metadata = { title: "Training · Dragon Academy" };

export default async function TrainActivityPage(props: PageProps<"/train/[activity]">) {
  const { activity } = await props.params;
  return <TrainActivity activityId={activity} />;
}
