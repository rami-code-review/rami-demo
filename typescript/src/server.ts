import { createApp } from "./app.js";

const port = parseInt(process.env.PORT ?? "3000", 10);
const app = createApp();

app.listen(port, () => {
  console.log(`task-manager listening on http://localhost:${port}`);
});
