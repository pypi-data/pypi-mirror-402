export interface FileNode {
	type: "file" | "folder" | "all_content";
	name: string;
	valid?: boolean;
}
