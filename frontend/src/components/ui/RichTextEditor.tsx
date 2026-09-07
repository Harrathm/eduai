import { useEditor, EditorContent, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import { TextStyle } from "@tiptap/extension-text-style";
import FontFamily from "@tiptap/extension-font-family";
import Color from "@tiptap/extension-color";
import Highlight from "@tiptap/extension-highlight";
import TextAlign from "@tiptap/extension-text-align";
import Link from "@tiptap/extension-link";
import Image from "@tiptap/extension-image";
import {
  Bold, Italic, Underline as UnderlineIcon, Strikethrough, Code,
  Heading1, Heading2, Heading3, List, ListOrdered, Quote, Link2,
  Image as ImageIcon, Undo2, Redo2, RemoveFormatting, AlignLeft,
  AlignCenter, AlignRight,
} from "lucide-react";

import { useState } from "react";

const FONT_SIZES = [
  { label: "Petit", value: "small" },
  { label: "Normal", value: "normal" },
  { label: "Grand", value: "x-large" },
];

const FONT_FAMILIES = [
  { label: "Système", value: "" },
  { label: "Serif", value: "serif" },
  { label: "Sans", value: "sans-serif" },
  { label: "Mono", value: "monospace" },
];

const TEXT_COLORS = ["#000000", "#ffffff", "#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899"];
const BG_COLORS = ["#fee2e2", "#fef3c7", "#dcfce7", "#dbeafe", "#ede9fe", "#fce7f3"];

interface RichTextEditorProps {
  value: string;
  onChange: (html: string, text: string) => void;
}

export function RichTextEditor({ value, onChange }: RichTextEditorProps) {
  const [html, setHtml] = useState(value || "");
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Underline,
      TextStyle,
      FontFamily,
      Color,
      Highlight.configure({ multicolor: true }),
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      Link.configure({ openOnClick: false, autolink: true, defaultProtocol: "https" }),
      Image.configure({ inline: false, allowBase64: true }),
    ],
    content: value || "<p></p>",
    onUpdate: ({ editor: ed }) => {
      const h = ed.getHTML();
      setHtml(h);
      onChange(h, ed.getText());
    },
    editorProps: {
      attributes: {
        class:
          "prose prose-sm max-w-none focus:outline-none min-h-[160px] max-h-[300px] overflow-y-auto px-4 py-3",
      },
    },
  });

  function setLink() {
    if (!editor) return;
    const previous = editor.getAttributes("link").href as string | undefined;
    const url = window.prompt("URL du lien:", previous || "https://");
    if (url === null) return;
    if (url === "") {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
      return;
    }
    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  }

  function addImage() {
    if (!editor) return;
    const url = window.prompt("URL de l'image:");
    if (!url) return;
    editor.chain().focus().setImage({ src: url }).run();
  }

  const ToolBtn = ({ onClick, active, title, children }: {
    onClick: () => void; active?: boolean; title: string; children: React.ReactNode;
  }) => (
    <button
      type="button"
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      title={title}
      className={`p-1.5 rounded hover:bg-cream disabled:opacity-40 ${active ? "bg-navy-50 text-navy-600" : "text-gray"}`}
    >
      {children}
    </button>
  );

  return (
    <div className="border rounded-xl overflow-hidden bg-white">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-1 p-2 border-b bg-cream-m/40 sticky top-0">
        <ToolBtn title="Annuler" onClick={() => editor?.chain().focus().undo().run()}><Undo2 className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Rétablir" onClick={() => editor?.chain().focus().redo().run()}><Redo2 className="w-4 h-4" /></ToolBtn>
        <div className="w-px h-5 bg-black/10 mx-1" />

        <ToolBtn title="Gras" active={editor?.isActive("bold")} onClick={() => editor?.chain().focus().toggleBold().run()}><Bold className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Italique" active={editor?.isActive("italic")} onClick={() => editor?.chain().focus().toggleItalic().run()}><Italic className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Souligné" active={editor?.isActive("underline")} onClick={() => editor?.chain().focus().toggleUnderline().run()}><UnderlineIcon className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Barré" active={editor?.isActive("strike")} onClick={() => editor?.chain().focus().toggleStrike().run()}><Strikethrough className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Code" active={editor?.isActive("code")} onClick={() => editor?.chain().focus().toggleCode().run()}><Code className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Effacer le format" onClick={() => editor?.chain().focus().unsetAllMarks().clearNodes().run()}><RemoveFormatting className="w-4 h-4" /></ToolBtn>
        <div className="w-px h-5 bg-black/10 mx-1" />

        <ToolBtn title="Titre 1" active={editor?.isActive("heading", { level: 1 })} onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}><Heading1 className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Titre 2" active={editor?.isActive("heading", { level: 2 })} onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}><Heading2 className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Titre 3" active={editor?.isActive("heading", { level: 3 })} onClick={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}><Heading3 className="w-4 h-4" /></ToolBtn>
        <div className="w-px h-5 bg-black/10 mx-1" />

        <ToolBtn title="Liste à puces" active={editor?.isActive("bulletList")} onClick={() => editor?.chain().focus().toggleBulletList().run()}><List className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Liste numérotée" active={editor?.isActive("orderedList")} onClick={() => editor?.chain().focus().toggleOrderedList().run()}><ListOrdered className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Citation" active={editor?.isActive("blockquote")} onClick={() => editor?.chain().focus().toggleBlockquote().run()}><Quote className="w-4 h-4" /></ToolBtn>
        <div className="w-px h-5 bg-black/10 mx-1" />

        <ToolBtn title="Aligné à gauche" active={editor?.isActive({ textAlign: "left" })} onClick={() => editor?.chain().focus().setTextAlign("left").run()}><AlignLeft className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Centré" active={editor?.isActive({ textAlign: "center" })} onClick={() => editor?.chain().focus().setTextAlign("center").run()}><AlignCenter className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Aligné à droite" active={editor?.isActive({ textAlign: "right" })} onClick={() => editor?.chain().focus().setTextAlign("right").run()}><AlignRight className="w-4 h-4" /></ToolBtn>
        <div className="w-px h-5 bg-black/10 mx-1" />

        <ToolBtn title="Lien" active={editor?.isActive("link")} onClick={setLink}><Link2 className="w-4 h-4" /></ToolBtn>
        <ToolBtn title="Image" onClick={addImage}><ImageIcon className="w-4 h-4" /></ToolBtn>

        <select
          title="Police"
          value={editor?.getAttributes("textStyle").fontFamily || ""}
          onChange={(e) => {
            const v = e.target.value;
            if (v) editor?.chain().focus().setFontFamily(v).run();
            else editor?.chain().focus().unsetFontFamily().run();
          }}
          className="p-1.5 rounded border border-black/10 bg-white text-sm ml-1"
        >
          {FONT_FAMILIES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>

        <select
          title="Taille"
          value={editor?.getAttributes("textStyle").fontSize || ""}
          onChange={(e) => {
            const v = e.target.value as "small" | "normal" | "x-large";
            if (!v) return;
            if (v === "normal") editor?.chain().focus().unsetFontSize().run();
            else editor?.chain().focus().setFontSize(v).run();
          }}
          className="p-1.5 rounded border border-black/10 bg-white text-sm"
        >
          {FONT_SIZES.map((s) => <option key={s.value} value={s.value === "normal" ? "" : s.value}>{s.label}</option>)}
        </select>

        <span className="w-px h-5 bg-black/10 mx-1" />

        {/* Text color */}
        <span className="flex items-center gap-0.5">
          {TEXT_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => editor?.chain().focus().setColor(c).run()}
              title={`Couleur ${c}`}
              className="w-4 h-4 rounded-full border border-black/20 hover:scale-110 transition-transform"
              style={{ background: c }}
            />
          ))}
        </span>

        {/* Highlight */}
        <span className="flex items-center gap-0.5 ml-1">
          {BG_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => editor?.chain().focus().toggleHighlight({ color: c }).run()}
              title={`Surbrillance ${c}`}
              className="w-4 h-4 rounded border border-black/20 hover:scale-110 transition-transform"
              style={{ background: c }}
            />
          ))}
        </span>
      </div>

      {/* Editor */}
      <EditorContent editor={editor} />

      <div className="px-4 py-2 text-xs text-gray-500 border-t bg-cream-m/40">
        <span className="inline-flex items-center gap-1"><ImageIcon className="w-3.5 h-3.5" /> Astuce: collez une URL d'image ou de vidéo, ou utilisez les boutons ci-dessus.</span>
      </div>
    </div>
  );
}
