if FORMAT ~= "latex" and FORMAT ~= "beamer" then
  return {}
end

local function trim(text)
  return (text:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function ensure_header_includes(meta, latex_snippet)
  local include = pandoc.MetaBlocks({ pandoc.RawBlock("latex", latex_snippet) })
  if meta["header-includes"] then
    table.insert(meta["header-includes"], include)
  else
    meta["header-includes"] = { include }
  end
end

local function is_simple_cell(cell)
  if cell.row_span ~= 1 or cell.col_span ~= 1 then
    return false
  end

  for _, block in ipairs(cell.contents) do
    if block.t ~= "Plain" and block.t ~= "Para" then
      return false
    end
  end
  return true
end

local function render_blocks_as_latex(blocks)
  local latex = pandoc.write(pandoc.Pandoc(blocks), "latex")
  latex = trim(latex)
  latex = latex:gsub("\r\n", "\n")
  latex = latex:gsub("\n+", " ")
  if latex == "" then
    return " "
  end
  return latex
end

local function column_alignment(colspec)
  local align = tostring(colspec[1])
  if align == "AlignRight" then
    return ">{\\raggedleft\\arraybackslash}"
  end
  if align == "AlignCenter" then
    return ">{\\centering\\arraybackslash}"
  end
  return ">{\\raggedright\\arraybackslash}"
end

local function build_column_spec(colspecs)
  local columns = {}
  local column_count = #colspecs
  local width_expr = "\\dimexpr\\linewidth/" .. tostring(column_count) .. "-2\\tabcolsep-2\\arrayrulewidth\\relax"
  for _, colspec in ipairs(colspecs) do
    table.insert(columns, column_alignment(colspec) .. "p{" .. width_expr .. "}")
  end
  return "|" .. table.concat(columns, "|") .. "|"
end

local function render_row(row)
  local rendered_cells = {}
  for _, cell in ipairs(row.cells) do
    if not is_simple_cell(cell) then
      return nil
    end
    table.insert(rendered_cells, render_blocks_as_latex(cell.contents))
  end
  return table.concat(rendered_cells, " & ") .. " \\\\ \\hline"
end

local function append_rendered_rows(lines, rows)
  for _, row in ipairs(rows) do
    local rendered = render_row(row)
    if rendered == nil then
      return false
    end
    table.insert(lines, rendered)
  end
  return true
end

function Meta(meta)
  ensure_header_includes(meta, "\\usepackage{longtable}")
  ensure_header_includes(meta, "\\usepackage{array}")
  ensure_header_includes(meta, "\\setlength{\\LTleft}{0pt}")
  ensure_header_includes(meta, "\\setlength{\\LTright}{0pt}")
  return meta
end

function Table(el)
  local lines = {
    "\\begin{longtable}{" .. build_column_spec(el.colspecs) .. "}",
    "\\hline",
  }

  if #el.caption.long > 0 then
    local caption = render_blocks_as_latex(el.caption.long)
    table.insert(lines, "\\caption{" .. caption .. "} \\\\ \\hline")
  end

  if #el.head.rows > 0 then
    if not append_rendered_rows(lines, el.head.rows) then
      return nil
    end
    table.insert(lines, "\\endfirsthead")
    table.insert(lines, "\\hline")
    if not append_rendered_rows(lines, el.head.rows) then
      return nil
    end
    table.insert(lines, "\\endhead")
  end

  for _, body in ipairs(el.bodies) do
    if #body.head > 0 and not append_rendered_rows(lines, body.head) then
      return nil
    end
    if not append_rendered_rows(lines, body.body) then
      return nil
    end
  end

  if #el.foot.rows > 0 and not append_rendered_rows(lines, el.foot.rows) then
    return nil
  end

  table.insert(lines, "\\end{longtable}")
  return pandoc.RawBlock("latex", table.concat(lines, "\n"))
end
