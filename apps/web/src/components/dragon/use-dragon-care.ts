"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api/client";
import { myDragonQueryKey, type PlayerDragon } from "@/lib/dragon/my-dragon";

export type Care = { action: "feed"; food: string } | { action: "rest" } | { action: "play" };

export function useDragonCare(
  dragon: PlayerDragon,
  userId: string,
  onReaction?: (action: Care["action"]) => void,
) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (care: Care) => {
      const params = { path: { dragon_id: dragon.id } };
      const { data, error } =
        care.action === "feed"
          ? await api.POST("/api/v1/dragons/{dragon_id}/feed", {
              params,
              body: { food: care.food },
            })
          : care.action === "rest"
            ? await api.POST("/api/v1/dragons/{dragon_id}/rest", { params })
            : await api.POST("/api/v1/dragons/{dragon_id}/play", { params });
      if (error || !data) throw new Error(error?.detail?.toString() ?? "Something went wrong");
      return data;
    },
    onSuccess: (result, care) => {
      client.setQueryData(myDragonQueryKey(userId), result.dragon);
      client.invalidateQueries({ queryKey: ["experience", dragon.id] });
      onReaction?.(care.action);
    },
  });
}
