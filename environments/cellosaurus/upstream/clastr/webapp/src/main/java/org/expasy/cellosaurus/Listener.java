package org.expasy.cellosaurus;

import org.expasy.cellosaurus.formats.Parser;
import org.expasy.cellosaurus.formats.xml.XmlParser;

import jakarta.servlet.ServletContextEvent;
import jakarta.servlet.ServletContextListener;
import java.io.IOException;


import org.expasy.cellosaurus.genomics.str.*;


/**
 * Class being executed once when the webapp is deployed. Its purpose is to parse the Cellosaurus cell lines with STR
 * profiles and store them in memory for subsequent searches.
 */
public class Listener implements ServletContextListener {

    /**
     * Read the XML version of the Cellosaurus database from the local read-only archive and store the human cell lines with STR profiles
     * and the database latest release information into the {@code Manager} as static variables.
     *
     * @param servletContextEvent the servlet context event
     */
    @Override
    public void contextInitialized(ServletContextEvent servletContextEvent) {
        try {

            String serverInfo = servletContextEvent.getServletContext().getServerInfo();
            System.out.println("Tomcat Server Info: " + serverInfo);            

            Parser parser = new XmlParser();
            // pam: see also code in XmlParser
            String file = System.getenv().getOrDefault("CELLOSAURUS_XML", "/data/cellosaurus.xml.gz");
            try (java.io.InputStream in = new java.util.zip.GZIPInputStream(new java.io.FileInputStream(file))) {
                parser.parse(in);
            }
            if (!"56.0".equals(org.expasy.cellosaurus.db.Database.CELLOSAURUS.getVersion())) {
                throw new IllegalStateException("Expected Cellosaurus release 56.0");
            }
            System.out.println("Done");

            showData();

        } catch (IOException e) {
            throw new IllegalStateException("Local Cellosaurus data failed to load", e);
        }
    }

    private void showData() {
        System.out.println("Data loaded from local release archive after parsing");
        System.out.println("HUMAN CellLines: " + Species.HUMAN.getCellLines().size());
        System.out.println("Mouse CellLines: " + Species.MOUSE.getCellLines().size());
        System.out.println("Dog   CellLines: " + Species.DOG.getCellLines().size());
    }
}
