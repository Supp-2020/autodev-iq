"use client";
import {
  Button,
  CardHeader,
  CardContent,
  CardActions,
  Card,
} from "@mui/material";
import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from 'next/navigation';

export const CardComponent = () => {

const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined") {
      router.prefetch("/semantic-search");
      router.prefetch("/test-generation");
      router.prefetch("/visual-regression");
    }
  }, [router]);
  return (
    <>
      <div className="flex justify-between card-container">
        <Card className="card">
          <CardHeader title={"Code-Aware AI Chat"} />
          <CardContent>
            {
              "AutoDev IQ gives you a smart chat assistant that understands your codebase.Ask about logic, structure, or the code flow diagram — and get responses tailored to your code’s context."
            }
          </CardContent>
          <CardActions
            sx={{
              display: "flex",
              justifyContent: "center",
              // marginTop: "auto",
            }}
          >
            <Link href={"/semantic-search"} passHref>
              <Button variant="contained" sx={{ padding: "14px 18px" }}>
                {"Semantic Search"}
              </Button>
            </Link>
          </CardActions>
        </Card>
        <Card className="card">
          <CardHeader title={"Auto-Generate Test Cases"} />
          <CardContent>
            {
              "Generate clean, ready-to-run unit tests in with AutoDev IQ  that reads your code, understands its logic, and delivers tests that saves development time, boosting code quality, and improving test coverage."
            }
          </CardContent>
          <CardActions
            sx={{
              display: "flex",
              justifyContent: "center",
              marginTop: "auto",
              marginBottom: "10px",
            }}
          >
            <Link href={"/test-generation"} passHref>
              <Button variant="contained" sx={{ padding: "14px 18px" }}>
                {"Test Generation"}
              </Button>
            </Link>
          </CardActions>
        </Card>

        <Card className="card">
          <CardHeader title={"Visual Regression Testing"} />
          <CardContent>
            {
              "Detect unintended UI changes with ease. Visual regression testing highlights layout shifts, style breaks, and other visual bugs — so you can catch them early and ship confidently."
            }
          </CardContent>
          <CardActions
            sx={{
              display: "flex",
              justifyContent: "center",
              marginTop: "auto",
              marginBottom: "10px",
            }}
          >
            <Link href={"/visual-regression"} passHref>
              <Button variant="contained" sx={{ padding: "14px 18px" }}>
                {"Visual Regression"}
              </Button>
            </Link>
          </CardActions>
        </Card>
      </div>
    </>
  );
};
