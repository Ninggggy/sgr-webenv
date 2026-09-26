package org.expasy.cellosaurus;

import com.google.gson.*;
import org.expasy.cellosaurus.formats.json.JsonFormatter;
import org.expasy.cellosaurus.formats.csv.CsvFormatter;
import org.expasy.cellosaurus.formats.xlsx.XlsxWriter;
import org.expasy.cellosaurus.formats.xml.XmlParser;
import org.expasy.cellosaurus.genomics.str.Species;
import org.expasy.cellosaurus.wrappers.Search;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.junit.jupiter.api.Test;
import jakarta.ws.rs.core.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ExportOrderTest {
 private JsonObject result() throws Exception {
  Species.HUMAN.getCellLines().clear();
  new XmlParser().parse(ClassLoader.getSystemResource("cellosaurus.min.xml").getPath());
  MultivaluedMap<String,String> p = new MultivaluedHashMap<>();
  String[][] values={{"Amel","X"},{"CSF1PO","13,14"},{"D5S818","10"},{"D7S820","8"},{"D13S317","11"},{"D16S539","8,9"},{"THO1","7,8"},{"TPOX","12"},{"vWA","10,11"},{"algorithm","3"},{"scoringMode","3"},{"maxResults","3"},{"scoreFilter","25"}};
  for(String[] v: values)p.add(v[0],v[1]);
  return new Gson().toJsonTree(Manager.search(p)).getAsJsonObject();
 }
 @Test void interleavedProfileOrderIsSharedByCsvAndXlsx() throws Exception {
  JsonObject json=result();Search original=new JsonFormatter().toSearch(json.toString());
  List<List<Integer>> order=original.getRowOrder();
  assertTrue(order.size()>3);assertTrue(original.getResults().get(0).getProfiles().size()>1);
  Collections.reverse(order);json.add("rowOrder",new Gson().toJsonTree(order));
  Search search=new JsonFormatter().toSearch(json.toString());
  String[] csv=new CsvFormatter().toCsv(search).split("\r\n");
  XlsxWriter writer=new XlsxWriter();
  try {
   writer.add(search);writer.write();
   try(XSSFWorkbook workbook=new XSSFWorkbook(writer.getXlsx())) {
    for(int i=0;i<order.size();i++) {
     List<Integer> pair=order.get(i);String ac=original.getResults().get(pair.get(0)).getAccession();
     String label=original.getResults().get(pair.get(0)).getProfiles().size()>1 ? (pair.get(1)==0?" Best":" Worst") : "";
     assertTrue(csv[i+2].startsWith("\""+ac+label));
     assertEquals(ac+label,workbook.getSheetAt(0).getRow(i+2).getCell(0).getStringCellValue().trim());
    }
   }
  } finally {writer.close();}
 }
 @Test void invalidOrPartialOrdersAreRejected() throws Exception {
  JsonObject json=result();Search original=new JsonFormatter().toSearch(json.toString());
  List<List<Integer>> order=original.getRowOrder();
  order.set(1,order.get(0));json.add("rowOrder",new Gson().toJsonTree(order));
  assertThrows(IllegalArgumentException.class,()->new JsonFormatter().toSearch(json.toString()));
  for(String bad:Arrays.asList("[]","[[0,0.5]]","[[0,999]]","null","{}","[[\"0\",0]]")) {
   json.add("rowOrder",new JsonParser().parse(bad));
   assertThrows(IllegalArgumentException.class,()->new JsonFormatter().toSearch(json.toString()));
  }
 }
}
