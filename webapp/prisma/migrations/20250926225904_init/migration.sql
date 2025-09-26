-- CreateTable
CREATE TABLE "bookmarks" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "url" TEXT NOT NULL,
    "title" TEXT,
    "description" TEXT,
    "domain" TEXT,
    "url_hash" TEXT NOT NULL,
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "imported_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "source" TEXT NOT NULL,
    "source_file" TEXT,
    "status" TEXT DEFAULT 'active',
    "favicon_url" TEXT,
    "screenshot_url" TEXT,
    "content_type" TEXT,
    "language" TEXT,
    "read_status" BOOLEAN DEFAULT false,
    "favorite" BOOLEAN DEFAULT false
);

-- CreateTable
CREATE TABLE "tags" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "color" TEXT DEFAULT '#6B7280',
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "usage_count" INTEGER DEFAULT 0
);

-- CreateTable
CREATE TABLE "bookmark_tags" (
    "bookmark_id" INTEGER NOT NULL,
    "tag_id" INTEGER NOT NULL,
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY ("bookmark_id", "tag_id"),
    CONSTRAINT "bookmark_tags_tag_id_fkey" FOREIGN KEY ("tag_id") REFERENCES "tags" ("id") ON DELETE CASCADE ON UPDATE NO ACTION,
    CONSTRAINT "bookmark_tags_bookmark_id_fkey" FOREIGN KEY ("bookmark_id") REFERENCES "bookmarks" ("id") ON DELETE CASCADE ON UPDATE NO ACTION
);

-- CreateTable
CREATE TABLE "collections" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "parent_id" INTEGER,
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "color" TEXT DEFAULT '#6B7280',
    "icon" TEXT,
    CONSTRAINT "collections_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "collections" ("id") ON DELETE SET NULL ON UPDATE NO ACTION
);

-- CreateTable
CREATE TABLE "bookmark_collections" (
    "bookmark_id" INTEGER NOT NULL,
    "collection_id" INTEGER NOT NULL,
    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY ("bookmark_id", "collection_id"),
    CONSTRAINT "bookmark_collections_collection_id_fkey" FOREIGN KEY ("collection_id") REFERENCES "collections" ("id") ON DELETE CASCADE ON UPDATE NO ACTION,
    CONSTRAINT "bookmark_collections_bookmark_id_fkey" FOREIGN KEY ("bookmark_id") REFERENCES "bookmarks" ("id") ON DELETE CASCADE ON UPDATE NO ACTION
);

-- CreateTable
CREATE TABLE "import_history" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "filename" TEXT NOT NULL,
    "file_path" TEXT NOT NULL,
    "file_hash" TEXT NOT NULL,
    "import_type" TEXT NOT NULL,
    "processed_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "bookmarks_imported" INTEGER DEFAULT 0,
    "bookmarks_skipped" INTEGER DEFAULT 0,
    "errors" TEXT
);

-- CreateTable
CREATE TABLE "bookmark_search" (
    "title" ,
    "description" ,
    "url" ,
    "tags" 
);

-- CreateTable
CREATE TABLE "bookmark_search_config" (
    "k"  NOT NULL PRIMARY KEY,
    "v" 
);

-- CreateTable
CREATE TABLE "bookmark_search_data" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "block" BLOB
);

-- CreateTable
CREATE TABLE "bookmark_search_docsize" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "sz" BLOB
);

-- CreateTable
CREATE TABLE "bookmark_search_idx" (
    "segid"  NOT NULL,
    "term"  NOT NULL,
    "pgno" ,

    PRIMARY KEY ("segid", "term")
);

-- CreateIndex
Pragma writable_schema=1;
CREATE UNIQUE INDEX "sqlite_autoindex_bookmarks_1" ON "bookmarks"("url");
Pragma writable_schema=0;

-- CreateIndex
Pragma writable_schema=1;
CREATE UNIQUE INDEX "sqlite_autoindex_bookmarks_2" ON "bookmarks"("url_hash");
Pragma writable_schema=0;

-- CreateIndex
CREATE INDEX "idx_bookmarks_url_hash" ON "bookmarks"("url_hash");

-- CreateIndex
CREATE INDEX "idx_bookmarks_source" ON "bookmarks"("source");

-- CreateIndex
CREATE INDEX "idx_bookmarks_created_at" ON "bookmarks"("created_at");

-- CreateIndex
CREATE INDEX "idx_bookmarks_domain" ON "bookmarks"("domain");

-- CreateIndex
CREATE INDEX "idx_bookmarks_url" ON "bookmarks"("url");

-- CreateIndex
Pragma writable_schema=1;
CREATE UNIQUE INDEX "sqlite_autoindex_tags_1" ON "tags"("name");
Pragma writable_schema=0;

-- CreateIndex
CREATE INDEX "idx_tags_name" ON "tags"("name");

-- CreateIndex
CREATE INDEX "idx_collections_parent_id" ON "collections"("parent_id");

-- CreateIndex
Pragma writable_schema=1;
CREATE UNIQUE INDEX "sqlite_autoindex_import_history_1" ON "import_history"("file_path", "file_hash");
Pragma writable_schema=0;
