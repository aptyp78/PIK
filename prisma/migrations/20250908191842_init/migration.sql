-- CreateTable
CREATE TABLE "SourceDoc" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "title" TEXT NOT NULL,
    "type" TEXT,
    "path" TEXT NOT NULL,
    "pages" INTEGER,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Block" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "sourceDocId" INTEGER NOT NULL,
    "page" INTEGER NOT NULL,
    "bbox" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "text" TEXT,
    "tableJson" TEXT,
    "hash" TEXT,
    CONSTRAINT "Block_sourceDocId_fkey" FOREIGN KEY ("sourceDocId") REFERENCES "SourceDoc" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Methodology" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "title" TEXT NOT NULL,
    "version" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "Frame" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "methodologyId" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "order" INTEGER,
    CONSTRAINT "Frame_methodologyId_fkey" FOREIGN KEY ("methodologyId") REFERENCES "Methodology" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Field" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "frameId" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "order" INTEGER,
    CONSTRAINT "Field_frameId_fkey" FOREIGN KEY ("frameId") REFERENCES "Frame" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "Block_sourceDocId_idx" ON "Block"("sourceDocId");

-- CreateIndex
CREATE INDEX "Block_page_idx" ON "Block"("page");

-- CreateIndex
CREATE INDEX "Block_text_idx" ON "Block"("text");

-- CreateIndex
CREATE UNIQUE INDEX "Methodology_title_version_key" ON "Methodology"("title", "version");

-- CreateIndex
CREATE UNIQUE INDEX "Frame_slug_key" ON "Frame"("slug");

-- CreateIndex
CREATE INDEX "Frame_methodologyId_idx" ON "Frame"("methodologyId");

-- CreateIndex
CREATE UNIQUE INDEX "Field_slug_key" ON "Field"("slug");

-- CreateIndex
CREATE INDEX "Field_frameId_idx" ON "Field"("frameId");
