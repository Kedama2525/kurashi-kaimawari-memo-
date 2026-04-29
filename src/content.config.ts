import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const articles = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/articles" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    slug: z.string(),
    category: z.string(),
    type: z.enum(["product-roundup", "marathon-guide", "economy-guide"]),
    date: z.string(),
    updated: z.string().optional(),
    eyecatch: z.string().optional(),
    affiliate: z.boolean().default(true),
    products: z.string().optional(),
    points: z.array(z.string()).default([]),
    related: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

const products = defineCollection({
  loader: glob({ pattern: "**/*.json", base: "./src/content/products" }),
  schema: z.array(
    z.object({
      name: z.string(),
      shortName: z.string(),
      priceText: z.string(),
      capacity: z.string(),
      shipping: z.string(),
      reviewCount: z.number().optional(),
      reviewAverage: z.number().optional(),
      imageUrl: z.url(),
      affiliateUrl: z.url(),
      features: z.array(z.string()).default([]),
      recommendedFor: z.string(),
      caution: z.string().optional(),
    }),
  ),
});

export const collections = {
  articles,
  products,
};
